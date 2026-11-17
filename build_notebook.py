import json
import os

cells = []

def md(text):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.split("\n")]
    })

def code(text):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.split("\n")]
    })

md("""# 1. Project Introduction

**Project Title:** Machine Learning-Based Email Spam and Phishing Detection System

**Purpose of the EDA:**
The goal of Exploratory Data Analysis (EDA) is to understand the structure, characteristics, and quality of our data before applying any Machine Learning algorithms. 

**Datasets:**
1. **Enron Spam Dataset:** Contains emails classified as Spam or Ham.
2. **PhiUSIIL Phishing URL Dataset:** Contains URLs classified as Legitimate or Phishing, along with numerous extracted features.

**Why EDA is necessary before Machine Learning:**
- To check for missing or duplicate values that can negatively impact model performance.
- To understand the class balance (e.g., if we have 99% legitimate URLs and 1% phishing, our model might be biased).
- To determine the distribution and scale of features to decide if we need scaling, normalization, or specialized preprocessing techniques.
- To identify which features might be strong predictors of Spam or Phishing.""")

md("""# 2. Import Libraries""")
code("""# Import required libraries
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set plotting style for clear visuals
sns.set_theme(style="whitegrid")

# Enable inline plotting for Jupyter Notebook
%matplotlib inline""")

md("""# 3. Project Paths""")
code("""# Get project root directory
# Assuming this notebook is located in project_root/notebooks/
BASE_DIR = os.path.dirname(os.path.abspath(""))

# Dataset paths
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
EMAIL_DATA_PATH = os.path.join(DATA_DIR, "enron_spam_data.csv")
URL_DATA_PATH = os.path.join(DATA_DIR, "PhiUSIIL_Phishing_URL_Dataset.csv")

# Output directory for EDA plots
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "eda")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Base Directory: {BASE_DIR}")
print(f"Email Data: {EMAIL_DATA_PATH}")
print(f"URL Data: {URL_DATA_PATH}")
print(f"Output Directory: {OUTPUT_DIR}")""")

md("""# 4. Email Spam/Ham Dataset""")

md("""## 4.1 Load Dataset""")
code("""print(f"Loading email dataset from: {EMAIL_DATA_PATH}")
try:
    df_email = pd.read_csv(EMAIL_DATA_PATH)
    print("Dataset loaded successfully!")
except FileNotFoundError:
    print("ERROR: Email dataset not found. Please check the path.")
except Exception as e:
    print(f"ERROR: {e}")""")

md("""## 4.2 Dataset Shape""")
code("""rows, columns = df_email.shape
print(f"Number of rows (emails): {rows}")
print(f"Number of columns (features): {columns}")""")

md("""## 4.3 Column Names""")
code("""print("Email Dataset Column Names:")
print(df_email.columns.tolist())""")

md("""## 4.4 Data Types""")
code("""print("Email Dataset Data Types:")
df_email.info()""")

md("""## 4.5 First 5 Records""")
code("""# Display the first 5 rows of the dataset
df_email.head()""")

md("""## 4.6 Missing Values""")
code("""missing_values = df_email.isnull().sum().sort_values(ascending=False)
print("Missing values per column:")
print(missing_values)
print(f"\\nTotal missing values in dataset: {missing_values.sum()}")""")

md("""## 4.7 Duplicate Records""")
code("""duplicate_rows = df_email.duplicated().sum()
print(f"Completely duplicate rows: {duplicate_rows}")
print(f"Duplicate percentage: {(duplicate_rows / len(df_email)) * 100:.2f}%")""")

md("""## 4.8 Identify Target Column""")
code("""# Identify the column containing our Spam/Ham labels
possible_target_columns = ["Spam/Ham", "spam", "label", "Label", "class", "Class"]
target_col = None

for column in possible_target_columns:
    if column in df_email.columns:
        target_col = column
        break

if target_col is None:
    print("WARNING: Could not automatically identify the target column.")
else:
    print(f"Target column identified as: '{target_col}'")""")

md("""## 4.9 Spam vs Ham Class Distribution""")
code("""class_distribution = df_email[target_col].value_counts(dropna=False)
print("Class Counts:")
print(class_distribution)

class_percentage = df_email[target_col].value_counts(normalize=True, dropna=False) * 100
print("\\nClass Percentage:")
print(class_percentage.round(2))""")

md("""## 4.10 Class Distribution Visualization""")
code("""plt.figure(figsize=(7, 5))
ax = sns.countplot(data=df_email, x=target_col)
plt.title("Email Dataset Class Distribution")
plt.xlabel("Email Class")
plt.ylabel("Number of Emails")

# Add count labels on bars
for container in ax.containers:
    ax.bar_label(container)

plt.tight_layout()

# Save plot
plot_path = os.path.join(OUTPUT_DIR, "email_class_distribution.png")
plt.savefig(plot_path, dpi=300)
print(f"Saved plot to: {plot_path}")
plt.show()""")

md("""## 4.11 Email Message Length Statistics""")
code("""# Identify message column
possible_message_columns = ["Message", "message", "Body", "body", "text", "Text"]
message_col = None

for column in possible_message_columns:
    if column in df_email.columns:
        message_col = column
        break

if message_col:
    print(f"Message column identified as: {message_col}")
    
    # Calculate length (filling missing with empty string to avoid errors)
    message_length = df_email[message_col].fillna("").astype(str).str.len()
    
    print("\\nMessage Length Statistics (in characters):")
    print(message_length.describe())
else:
    print("No message/body column found.")""")

md("""## 4.12 Email Length Visualization""")
code("""if message_col:
    plot_df = pd.DataFrame({
        "message_length": message_length,
        "email_class": df_email[target_col]
    })
    
    # Filter out extremely long emails for a cleaner histogram
    plot_df_filtered = plot_df[plot_df["message_length"] < 10000]
    
    plt.figure(figsize=(10, 6))
    sns.histplot(data=plot_df_filtered, x="message_length", hue="email_class", bins=50, kde=True, element="step")
    plt.title("Distribution of Email Message Length by Class")
    plt.xlabel("Message Length (Characters)")
    plt.ylabel("Number of Emails")
    plt.tight_layout()
    
    plot_path = os.path.join(OUTPUT_DIR, "email_message_length_distribution.png")
    plt.savefig(plot_path, dpi=300)
    print(f"Saved plot to: {plot_path}")
    plt.show()
    
    # Print average length by class
    print("\\nAverage Email Length by Class:")
    print(plot_df.groupby("email_class")["message_length"].agg(["count", "mean", "median", "max"]))""")

md("""## 4.13 Subject Length Analysis if Subject exists""")
code("""possible_subject_columns = ["Subject", "subject"]
subject_col = None

for column in possible_subject_columns:
    if column in df_email.columns:
        subject_col = column
        break

if subject_col:
    print(f"Subject column identified as: {subject_col}")
    subject_length = df_email[subject_col].fillna("").astype(str).str.len()
    
    print("\\nSubject Length Statistics:")
    print(subject_length.describe())
    
    subject_plot_df = pd.DataFrame({
        "subject_length": subject_length,
        "email_class": df_email[target_col]
    })
    
    plt.figure(figsize=(10, 6))
    sns.histplot(data=subject_plot_df, x="subject_length", hue="email_class", bins=40, kde=True, element="step")
    plt.title("Distribution of Email Subject Length by Class")
    plt.xlabel("Subject Length (Characters)")
    plt.ylabel("Number of Emails")
    plt.tight_layout()
    
    plot_path = os.path.join(OUTPUT_DIR, "email_subject_length_distribution.png")
    plt.savefig(plot_path, dpi=300)
    print(f"Saved plot to: {plot_path}")
    plt.show()
else:
    print("No subject column found.")""")

md("""## Email Dataset Observations

- Number of emails: [PLACEHOLDER]
- Number of columns: [PLACEHOLDER]
- Missing values: [PLACEHOLDER]
- Duplicate records: [PLACEHOLDER]
- Spam samples: [PLACEHOLDER]
- Ham samples: [PLACEHOLDER]
- Class balance: [PLACEHOLDER]
- Average email length: [PLACEHOLDER]
- Median email length: [PLACEHOLDER]""")

md("""# 5. PhiUSIIL Phishing URL Dataset""")

md("""## 5.1 Load Dataset""")
code("""print(f"Loading URL dataset from: {URL_DATA_PATH}")
try:
    df_url = pd.read_csv(URL_DATA_PATH)
    print("Dataset loaded successfully!")
except FileNotFoundError:
    print("ERROR: URL dataset not found. Please check the path.")
except Exception as e:
    print(f"ERROR: {e}")""")

md("""## 5.2 Dataset Shape""")
code("""rows, columns = df_url.shape
print(f"Number of rows (URLs): {rows}")
print(f"Number of columns (features): {columns}")""")

md("""## 5.3 All Column Names""")
code("""print("URL Dataset Column Names:")
for index, column in enumerate(df_url.columns, start=1):
    print(f"{index}. {column}")""")

md("""## 5.4 Data Types""")
code("""print("URL Dataset Data Types Summary:")
print(df_url.dtypes.value_counts())""")

md("""## 5.5 First 5 Records""")
code("""# Display the first 5 records of the URL dataset
df_url.head()""")

md("""## 5.6 Missing Values""")
code("""missing_values = df_url.isnull().sum().sort_values(ascending=False)
missing_columns = missing_values[missing_values > 0]

if missing_columns.empty:
    print("No missing values found.")
else:
    print("Missing values per column:")
    print(missing_columns)
    print(f"\\nTotal missing values: {missing_values.sum()}")""")

md("""## 5.7 Duplicate Records""")
code("""duplicate_rows = df_url.duplicated().sum()
print(f"Completely duplicate rows: {duplicate_rows}")
print(f"Duplicate percentage: {(duplicate_rows / len(df_url)) * 100:.2f}%")""")

md("""## 5.8 Identify Target Column""")
code("""possible_target_columns = ["label", "Label", "class", "Class", "phishing", "Phishing", "Result"]
target_col_url = None

for column in possible_target_columns:
    if column in df_url.columns:
        target_col_url = column
        break

if target_col_url is None:
    print("WARNING: Could not automatically identify the URL target column.")
else:
    print(f"Target column identified as: '{target_col_url}'")""")

md("""## 5.9 Identify URL Column""")
code("""possible_url_columns = ["URL", "url", "Url", "Domain", "domain"]
url_col = None

for column in possible_url_columns:
    if column in df_url.columns:
        url_col = column
        break

print(f"URL column identified as: {url_col}")""")

md("""## 5.10 Legitimate vs Phishing Distribution""")
code("""class_distribution = df_url[target_col_url].value_counts(dropna=False)
print("Class Counts:")
print(class_distribution)

class_percentage = df_url[target_col_url].value_counts(normalize=True, dropna=False) * 100
print("\\nClass Percentage:")
print(class_percentage.round(2))""")

md("""## 5.11 Class Distribution Visualization""")
code("""plt.figure(figsize=(7, 5))
ax = sns.countplot(data=df_url, x=target_col_url)
plt.title("URL Dataset Class Distribution")
plt.xlabel("URL Class")
plt.ylabel("Number of URLs")

for container in ax.containers:
    ax.bar_label(container)

plt.tight_layout()
plot_path = os.path.join(OUTPUT_DIR, "url_class_distribution.png")
plt.savefig(plot_path, dpi=300)
print(f"Saved plot to: {plot_path}")
plt.show()""")

md("""## 5.12 Numerical Feature Summary""")
code("""numerical_columns = df_url.select_dtypes(include=["number"]).columns.tolist()

if target_col_url in numerical_columns:
    numerical_columns.remove(target_col_url)

print(f"Number of numerical features: {len(numerical_columns)}")

# Show summary statistics for numerical features (transposed for readability)
df_url[numerical_columns].describe().T""")

md("""## 5.13 Important URL Feature Distributions""")
code("""preferred_features = [
    "URLLength", "DomainLength", "NoOfDots", "NoOfHyphen", "NoOfSubDomain",
    "NoOfSpecialChars", "NoOfDigits", "HasHTTPS", "URLCharProb", "TLDLegitimateProb"
]

available_features = [f for f in preferred_features if f in df_url.columns]

print(f"Found {len(available_features)} predefined important features.")

features_to_plot = available_features[:6] # Plot max 6 features

for feature in features_to_plot:
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df_url, x=feature, hue=target_col_url, bins=30, kde=True, element="step")
    plt.title(f"Distribution of {feature} by URL Class")
    plt.xlabel(feature)
    plt.ylabel("Number of URLs")
    plt.tight_layout()
    
    safe_feature_name = feature.replace("/", "_")
    plot_path = os.path.join(OUTPUT_DIR, f"url_feature_{safe_feature_name}.png")
    plt.savefig(plot_path, dpi=300)
    plt.show()""")

md("""## 5.14 Correlation Analysis""")
code("""correlation_features = numerical_columns[:15] # Limit to 15 to keep it readable

if len(correlation_features) >= 2:
    correlation_matrix = df_url[correlation_features].corr()
    
    plt.figure(figsize=(14, 10))
    sns.heatmap(correlation_matrix, annot=False, cmap="coolwarm", center=0)
    plt.title("Correlation Heatmap of Selected URL Features")
    plt.tight_layout()
    
    plot_path = os.path.join(OUTPUT_DIR, "url_feature_correlation_heatmap.png")
    plt.savefig(plot_path, dpi=300)
    print(f"Saved correlation heatmap to: {plot_path}")
    plt.show()
else:
    print("Not enough numerical features for correlation analysis.")""")

md("""## URL Dataset Observations

- Number of URLs: [PLACEHOLDER]
- Number of features: [PLACEHOLDER]
- Missing values: [PLACEHOLDER]
- Duplicate records: [PLACEHOLDER]
- Phishing samples: [PLACEHOLDER]
- Legitimate samples: [PLACEHOLDER]
- Class balance: [PLACEHOLDER]""")

md("""# 6. EDA Conclusions

*(Fill this in after running the notebook)*

### 1. Data Quality and Next Steps for Emails
- [PLACEHOLDER for what needs to be cleaned/preprocessed in emails]

### 2. Data Quality and Next Steps for URLs
- [PLACEHOLDER for what needs to be cleaned/preprocessed in URLs]

### 3. Machine Learning Strategy
- [PLACEHOLDER for how imbalanced the data is and whether we need class balancing techniques]
- [PLACEHOLDER for whether we need to extract additional features]""")

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.8"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(os.path.join("c:\\\\Users\\\\admin\\\\Desktop\\\\ML CP", "notebooks", "01_EDA.ipynb"), "w") as f:
    json.dump(notebook, f, indent=1)

print("Notebook generated successfully!")
