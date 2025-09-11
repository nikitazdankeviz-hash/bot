from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Каталог", callback_data="catalog")
    kb.button(text="Корзина", callback_data="cart")
    kb.adjust(2)
    return kb

def categories_kb(categories):
    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=c["title"], callback_data=f"cat:{c['id']}")
    kb.button(text="⬅️ Назад", callback_data="back_to_menu")
    kb.adjust(2)
    return kb

def products_kb(products, cat_id):
    kb = InlineKeyboardBuilder()
    for p in products:
        if not p.get("active", True): 
            continue
        kb.button(text=f"{p['title']} — {int(p['price_rub'])}₽", callback_data=f"prod:{p['id']}")
    kb.button(text="⬅️ Категории", callback_data="catalog")
    kb.adjust(1)
    return kb

def product_kb(prod_id: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить в корзину", callback_data=f"add:{prod_id}:1")
    kb.button(text="⬅️ Назад", callback_data="catalog")
    kb.adjust(1,1)
    return kb

def cart_kb(has_items: bool):
    kb = InlineKeyboardBuilder()
    if has_items:
        kb.button(text="Оформить заказ", callback_data="checkout")
        kb.button(text="Очистить", callback_data="cart_clear")
    kb.button(text="⬅️ Меню", callback_data="back_to_menu")
    kb.adjust(2 if has_items else 1, 1)
    return kb

def admin_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Курс", callback_data="admin:rate")
    kb.button(text="Каталог JSON", callback_data="admin:products")
    kb.button(text="Заказы", callback_data="admin:orders")
    kb.button(text="Экспорт CSV", callback_data="admin:export")
    kb.adjust(2,2)
    return kb
