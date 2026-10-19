@'
# Dataset

RetailOps uses the Brazilian E-Commerce Public Dataset by Olist.

Source:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

The dataset covers historical Brazilian e-commerce activity from
2016 to 2018. See the source page for the full dataset description
and licence: CC BY-NC-SA 4.0.

Download the CSV files yourself and place the required files in
data/raw/olist/. The raw dataset is not committed to this repository.

RetailOps inventory quantities are simulated separately and must
not be interpreted as actual Olist stock records.
'@ | Set-Content -Encoding utf8 .\data\README.md