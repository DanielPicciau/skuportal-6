from decimal import Decimal

# Platform fee settings (Vinted defaults)
VINTED_FEE_PERCENT = Decimal('0.05')  # 5%
VINTED_FIXED_FEE = Decimal('0.70')    # £0.70

# Customize these lists as needed
CATEGORIES = [
    'Clothing', 'Shoes', 'Accessories', 'Bags', 'Jewelry', 'Beauty', 'Kids', 'Home', 'Electronics', 'Other'
]

CONDITIONS = [
    'New with tags', 'New without tags', 'Like new', 'Good', 'Fair', 'Poor', 'Vintage', 'Defective'
]

STATUSES = [
    'Draft', 'To Photograph', 'To List', 'Listed', 'Reserved', 'Sold', 'Returned', 'Donated'
]

