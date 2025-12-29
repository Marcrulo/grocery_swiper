# %% [markdown]
# # Imports

# %%
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import pandas as pd
import datetime
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import KNeighborsClassifier

import sqlite3

from dotenv import load_dotenv

load_dotenv()

# %% [markdown]
# # Calculate top items

# %% [markdown]
# ## Load data

# %%
CSV_PATH = "../data/csv/processed/"
files    = os.listdir(CSV_PATH)
csvs     = sorted([file.split('_')[1].split('.')[0] for file in files])

historic_csvs = csvs[:-1]
train_df      = pd.concat([pd.read_csv(f"{CSV_PATH}products_{csv}.csv") for csv in historic_csvs], ignore_index=True)

latest_csv = csvs[-1]
test_df    = pd.read_csv(f"{CSV_PATH}products_{latest_csv}.csv")

# %%
conn = sqlite3.connect("../data/sql/download")
labels = pd.read_sql_query("SELECT data_id, is_liked, is_superliked, is_passed FROM swipes WHERE device_id = 'wvh6mq'", conn)
conn.close()

# %% [markdown]
# ## Pre-processing

# %%
stop_words = ['i','på','og','til']
vectorizer = CountVectorizer(binary=True, lowercase=True, stop_words=stop_words)
train_sentences = train_df['product_name'].tolist()
train_product_encoding = vectorizer.fit_transform(train_sentences).toarray()

test_sentences = test_df['product_name'].tolist()
test_product_encoding = vectorizer.transform(test_sentences).toarray()

# %%
onehot = ['brand','category']
preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown='ignore'), onehot),
    ("num", StandardScaler(), ['price'])
])
train_onehot = preprocessor.fit_transform(train_df).toarray()
test_onehot  = preprocessor.transform(test_df).toarray()
num_categories = sum(len(c) for c in preprocessor.named_transformers_['cat'].categories_)
print(f"Number of categories after one-hot encoding: {num_categories}")

# %%
train_preprocessed = np.hstack((train_product_encoding, train_onehot))
test_preprocessed  = np.hstack((test_product_encoding, test_onehot))

train_df_preprocessed = pd.DataFrame(train_preprocessed, columns=[f"feature_{i}" for i in range(train_preprocessed.shape[1])])
train_df_preprocessed = pd.merge(train_df, train_df_preprocessed, left_index=True, right_index=True)

test_df_preprocessed = pd.DataFrame(test_preprocessed, columns=[f"feature_{i}" for i in range(test_preprocessed.shape[1])])
test_df_preprocessed = pd.merge(test_df, test_df_preprocessed, left_index=True, right_index=True)

# %%
train_df_features = train_df_preprocessed.iloc[:, len(train_df.columns):]
train_df_features['data_id'] = train_df_preprocessed['data_id']
train_df_features = pd.merge(train_df_features, labels, on='data_id', how='inner')

Xtrain = train_df_features.drop(columns=['data_id', 'is_liked', 'is_superliked', 'is_passed']).to_numpy()
ytrain = (train_df_features['is_liked'] | train_df_features['is_superliked']).to_numpy()

test_df_features  = test_df_preprocessed.iloc[:, len(test_df.columns):]
test_df_features['data_id'] = test_df_preprocessed['data_id']

Xtest = test_df_features.drop(columns=['data_id']).to_numpy()

# %% [markdown]
# ## Inference

# %%
knn = KNeighborsClassifier(n_neighbors=5, metric='cosine')

# Duplicate samples based on weights
weights = np.where(train_df_features['is_superliked'] == 1, 3, 1)

# Repeat each row according to its weight
indices = np.repeat(np.arange(len(train_df_features)), weights)

Xtrain_weighted = Xtrain[indices]
ytrain_weighted = ytrain[indices]
train_df_features_weighted = train_df_features.iloc[indices].reset_index(drop=True)

knn.fit(Xtrain_weighted, ytrain_weighted)

# %%
# Probabilities for all test samples, and print in descending order of probability of being liked
probas = knn.predict_proba(Xtest)
sorted_indices = np.argsort(-probas[:, 1])  # Sort by probability of being liked (class 1)
for idx in sorted_indices:
    data_id = test_df_features.iloc[idx]['data_id']
    product_name = test_df[test_df['data_id'] == data_id]['product_name'].values[0]
    print(f"{probas[idx, 1]:.4f} {product_name}")



# %%
# Build reordered DataFrame of test_df with probabilities
# Uses existing variables: probas, sorted_indices, test_df
ordered_indices = sorted_indices.copy()
test_df_ordered = test_df.iloc[ordered_indices].copy()
test_df_ordered['probability'] = probas[ordered_indices, 1]

final_df = test_df_ordered[test_df_ordered['probability']>0.5]
final_df.to_csv("../data/csv/mail_groceries.csv", index=False) 

# %% [markdown]
# # Send EMAIL

# %%
# Email configuration
SMTP_SERVER = "smtp.gmail.com"  # For Gmail
SMTP_PORT = 587  # TLS port

# Get credentials from environment variables
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Use app password for Gmail

# Verify credentials are loaded
if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    print("Warning: EMAIL_ADDRESS and EMAIL_PASSWORD must be set in your .env file")
else:
    print(f"Email configured for: {EMAIL_ADDRESS}")

# %%
def send_html_email(to_email, subject, html_body):
    """Send an email with HTML content."""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Connect and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✓ HTML email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False

# %%

CSV_PATH = "../data/csv/mail_groceries.csv"


def build_grocery_grid_html(csv_path=CSV_PATH, period_text=None):
    """Return an HTML string with a 2-column grid for email.
    If period_text is provided, it is shown at the top of the email.
    """
    df = pd.read_csv(csv_path)
    df = df.fillna("")

    def card_html(row):
        img = row.get("public_urls", "") or row.get("image_url", "")
        name = row.get("product_name") or row.get("translated_product") or "Item"
        brand = row.get("brand", "")
        price = row.get("price", "")
        store = row.get("store_name", "")
        quantity = row.get("quantity", "")
        unit_type = row.get("unit_type", "")
        units = row.get("units", "")

        price_display = f"{float(price):.2f},-" if price != "" else ""
        qty = f"{quantity} {unit_type}".strip() if quantity != "" else ""
        unit = f"{units}x {qty}" if units not in ["", None] else qty

        optional_brand = f"<div style='font-size:12px;color:#666;margin-top:4px;'>{brand}</div>" if brand else ""
        optional_unit = f"<div style='font-size:12px;color:#666;'>{unit}</div>" if unit else ""
        img_tag = (
            f"<img src='{img}' alt='{name}' style='width:100%;height:180px;object-fit:cover;border-radius:8px 8px 0 0;'/>"
            if img
            else "<div style='height:180px;background:#eee;border-radius:8px 8px 0 0;'></div>"
        )

        return f"""
                <div style='border:1px solid #e5e5e5;border-radius:10px;overflow:hidden;font-family:Arial, sans-serif;background:#fff;'>
                  {img_tag}
                  <div style='padding:10px;'>
                    <div style='font-weight:600;font-size:14px;color:#222;'>{name}</div>
                    {optional_brand}
                    <div style='font-size:13px;color:#111;margin-top:6px;'>{price_display}</div>
                    <div style='font-size:12px;color:#666;'>{store}</div>
                  </div>
                </div>
                """

    cards = [card_html(row) for _, row in df.iterrows()]

    rows = []
    for i in range(0, len(cards), 2):
        chunk = cards[i : i + 2]
        cells = "".join(
            f"<td style='padding:8px;vertical-align:top;width:50%;'>" + card + "</td>" for card in chunk
        )
        rows.append(f"<tr>{cells}</tr>")

    table_rows = "\n".join(rows)

    # Optional sales period block at the top
    period_block = (
        f"<p style='color:#222;margin:0 0 12px 0;font-weight:600;'>" + period_text + "</p>"
        if period_text else ""
    )

    html = f"""
            <html>
              <body style='margin:0;padding:16px;background:#f7f7f7;font-family:Arial,sans-serif;'>
                <div style='max-width:960px;margin:0 auto;'>
                  {period_block}
                  <p style='color:#444;margin-top:0;margin-bottom:16px;'>Curated picks from this week's sales flyer based on your preferences.</p>
                  <table role='presentation' cellpadding='0' cellspacing='0' border='0' style='border-collapse:collapse;width:100%;table-layout:fixed;'>
                    {table_rows}
                  </table>
                </div>
              </body>
            </html>
            """
    return html



# %%
# Build HTML for topitems (2-column grid) with sales period at top

# Compute period from latest_csv (YYYY-MM-DD) to +6 days
try:
    start_date = datetime.strptime(latest_csv, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=6)
    period_text = f"Sales in period {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"
except Exception:
    period_text = None

try:
    html_content = build_grocery_grid_html(period_text=period_text)
    preview = html_content[:500] + ("..." if len(html_content) > 500 else "")
    print("HTML preview (first 500 chars):")
    print(preview)
except FileNotFoundError:
    html_content = ""
    print("CSV not found at ../data/csv/mail_groceries.csv")

subject_line = f"Weekly Grocery Highlights — {datetime.today().strftime('%Y-%m-%d')}"

# send_html_email(
#     to_email="thorupmettek@gmail.com ",
#     subject=subject_line,
#     html_body=html_content
# )
send_html_email(
    to_email="marcus.presutti.eu@gmail.com",
    subject=subject_line,
    html_body=html_content
)



