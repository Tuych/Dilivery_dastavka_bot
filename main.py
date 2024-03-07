from telegram import (Update,InlineKeyboardButton,InlineKeyboardMarkup,KeyboardButton,
                      ReplyKeyboardMarkup)
from telegram.ext import (ApplicationBuilder,CommandHandler,CallbackQueryHandler,
                          MessageHandler,filters)
from datetime import datetime
from project.db import DB
from project.globals import TEXTS
from geopy.geocoders import Nominatim


db=DB()


async def start(update,context):
    user=update.message.from_user
    user_data=db.get_user(user.id)
    
    if not user_data:
        user_data=db.add_user(user.id, user.first_name, user.username)
        state=db.get_state(user_data['id'])
        if not state:
            state=db.add_state(user_data['id'],1)

        lang_button = [
                [
            InlineKeyboardButton("🇺🇿 Uzbek", callback_data='lang_1'),
            InlineKeyboardButton("🇷🇺 Russian", callback_data='lang_2'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_3'),]
            ]

        await update.message.reply_text(f"Assalom alaykum xush kelibsiz,Tilni tanlang\n\n"
                                        f"Здравствуйте, добро пожаловать, выберите язык\n\n"
                                        f"Hello, welcome, choose a language\n",
                                                        reply_markup=InlineKeyboardMarkup(lang_button))
    
    else:
        if not user_data['lang']:
            state=db.get_state(user_data['id'])
            if not state:
                state=db.add_state(user_data['id'],1)

            lang_button = [
                [
            InlineKeyboardButton("🇺🇿 Uzbek", callback_data='lang_1'),
            InlineKeyboardButton("🇷🇺 Russian", callback_data='lang_2'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_3'),]
            ]

            await update.message.reply_text("Assalom alaykum xush kelibsiz !!!\n\nTilni tanlang👇",
                                                    reply_markup=InlineKeyboardMarkup(lang_button))

        elif not user_data['name']:
            db.add_state(user_data['id'],2)
            await update.message.reply_text(TEXTS['TEXT_NAME'][user_data['lang']])

        elif not user_data['phone_number']:
            button=[
            [KeyboardButton(TEXTS["BTN_PHONE_NUMBER"][user_data['lang']],request_contact=True)]
            ]
            db.add_state(user_data['id'],3)
            await update.message.reply_text(TEXTS["TEXT_PHONE_NUMBER"][user_data['lang']],reply_markup=ReplyKeyboardMarkup(button,resize_keyboard=True))

        else:
            db.clear_bucket(user_data['id'])
            buttons=[
                [KeyboardButton(TEXTS["BTN_ORDER"][user_data['lang']]),
                KeyboardButton(TEXTS["BTN_MY_ORDER"][user_data['lang']])],
                [KeyboardButton(TEXTS["BTN_FILIAL"][user_data['lang']])]
            ]
            db.add_state(user_data['id'],4)
            await update.message.reply_text(TEXTS['TEXT_MAIN_MENYU'][user_data['lang']],
                                            reply_markup=ReplyKeyboardMarkup(buttons,resize_keyboard=True))

                    






    
async def query_handler(update,context):
    user=update.callback_query.from_user
    data=update.callback_query.data
    data=data.split('_')
    print(data)
    user_data=db.get_user(user.id)
    lang=user_data['lang']
    state=db.get_state(user_data['id'])
    message_id=update.callback_query.message.message_id


    if data[0]=='lang':
        user_data=db.update_user(user_data['id'],lang=data[1])
        db.add_state(user_data['id'],2)
        await context.bot.delete_message(chat_id=user.id,message_id=message_id)
        await update.callback_query.message.reply_text(TEXTS['TEXT_NAME'][user_data['lang']])


    elif data[0]=='category':
        products=db.get_all_product(int(data[1]))
        products_button=[]
        temp_button=[]


        for product in products:
            temp_button.append(InlineKeyboardButton(text=product['name'],
                                                    callback_data=f"product_{product['id']}"))
            if len(temp_button)==2:
                products_button.append(temp_button)
                temp_button=[]
        if len(temp_button)>=1:
            products_button.append(temp_button)

        if db.get_bucket_items(user_data['id']):
            products_button.append([InlineKeyboardButton(TEXTS["BTN_BUCKET"][lang],callback_data='bucket_view')])

        products_button.append([InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='product_back')])

        category=db.get_one_category(int(data[1]))


        await context.bot.delete_message(chat_id=user.id,message_id=message_id)

        await update.callback_query.message.reply_photo(photo=open(category['photo'],'rb'),
                                                        caption=category['name'],
                                                        reply_markup=InlineKeyboardMarkup(products_button))


    elif data[0]=="product":
        if data[1]=='back':
            categories=db.get_all_caregory()
            
            category_button=[]
            temp_button=[]

            for category in categories:
                temp_button.append(InlineKeyboardButton(text=category['name'],callback_data=f"category_{category['id']}"))

                if len(temp_button)==2:
                    category_button.append(temp_button)
                    temp_button=[]

            if len(temp_button)>=1:
                category_button.append(temp_button)

            if db.get_bucket_items(user_data['id']):
                category_button.append([InlineKeyboardButton(TEXTS["BTN_BUCKET"][lang],callback_data='bucket_view')])

            await context.bot.delete_message(chat_id=user.id,message_id=message_id)
            await update.callback_query.message.reply_text(f"""{TEXTS["CATEGORY_SECTION"][lang]}<a href="https://telegra.ph/Taomnoma-09-30">.</a>""",
                                            reply_markup=InlineKeyboardMarkup(category_button),parse_mode="HTML")
        
        else:
            product=db.get_one_product(int(data[1]))


            product_button=[
                [
                    InlineKeyboardButton("➖",callback_data=f"bucket_minus_{product['id']}_1"),
                    InlineKeyboardButton("1",callback_data="count"),
                    InlineKeyboardButton("➕",callback_data=f"bucket_plus_{product['id']}_1")
                ],
                [InlineKeyboardButton(TEXTS["BTN_ADD_BUCKET"][lang],callback_data=f"bucket_add_{product['id']}_1")],

                [InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data=f"bucket_back_{product['id']}")]
                
            ]

            if db.get_bucket_items(user_data['id']):
                product_button[2].append(InlineKeyboardButton(TEXTS["BTN_BUCKET"][lang],callback_data='bucket_view'))


            caption_text=TEXTS["TEXT_PRODUCT_CAPTION"][lang]%(product['name'],product['price'],product['description'])
            await context.bot.delete_message(chat_id=user.id,message_id=message_id)
            await update.callback_query.message.reply_photo(photo=open(product['photo'],'rb'),
                                                            caption=caption_text,
                                                            reply_markup=InlineKeyboardMarkup(product_button))


    elif data[0]=='bucket':
        if data[1]=='plus':
            product=db.get_one_product(int(data[2]))
            product_count=int(data[3])+1

            product_button=[
            [
                InlineKeyboardButton("➖",callback_data=f"bucket_minus_{product['id']}_{ product_count}"),
                InlineKeyboardButton(str(product_count),callback_data="count"),
                InlineKeyboardButton("➕",callback_data=f"bucket_plus_{product['id']}_{ product_count}")
            ],
            [InlineKeyboardButton(TEXTS["BTN_ADD_BUCKET"][lang],callback_data=f"bucket_add_{product['id']}_{ product_count}")],

            [InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data=f"bucket_back_{product['id']}")]

            
            ]

            if db.get_bucket_items(user_data['id']):
                product_button[2].append(InlineKeyboardButton(TEXTS["BTN_BUCKET"][lang],callback_data='bucket_view'))

            caption_text=TEXTS["TEXT_PRODUCT_CAPTION"][lang]%(product['name'],f"{product['price']}✖️{product_count}🟰{int(product['price'])*product_count}",product['description'])
            await context.bot.edit_message_caption(chat_id=user.id,message_id=message_id,
                                               caption=caption_text,
                                               reply_markup=InlineKeyboardMarkup(product_button))
        


        elif data[1]=='minus':
            product=db.get_one_product(int(data[2]))
            if int(data[3])>1:
                product_count=int(data[3])-1

                product_button=[
                [
                    InlineKeyboardButton("➖",callback_data=f"bucket_minus_{product['id']}_{ product_count}"),
                    InlineKeyboardButton(str(product_count),callback_data="count"),
                    InlineKeyboardButton("➕",callback_data=f"bucket_plus_{product['id']}_{ product_count}")
                ],
                [InlineKeyboardButton(TEXTS["BTN_ADD_BUCKET"][lang],callback_data=f"bucket_add_{product['id']}_{ product_count}")],

                [InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data=f"bucket_back_{product['id']}")]
               
                ]

                if db.get_bucket_items(user_data['id']):
                    product_button[2].append(InlineKeyboardButton(TEXTS["BTN_BUCKET"][lang],callback_data='bucket_view'))
                caption_text=TEXTS["TEXT_PRODUCT_CAPTION"][lang]%(product['name'],f"{product['price']}✖️{product_count}🟰{int(product['price'])*product_count}",product['description'])
                await context.bot.edit_message_caption(chat_id=user.id,message_id=message_id,
                                                caption=caption_text,
                                                reply_markup=InlineKeyboardMarkup(product_button))
            
        elif data[1]=='add':
            product=db.get_one_product(int(data[2]))
            product_count=int(data[3])
            bucket=db.get_or_create_bucket(user_data['id'])
            db.create_or_update_bucket_item(product['id'],int(data[3]),bucket['bucket_id'])

            products=db.get_all_product(product['category_id'])
            products_button=[]
            temp_button=[]


            for product in products:
                temp_button.append(InlineKeyboardButton(text=product['name'],
                                                        callback_data=f"product_{product['id']}"))
                if len(temp_button)==2:
                    products_button.append(temp_button)
                    temp_button=[]
            if len(temp_button)>=1:
                products_button.append(temp_button)

            products_button.append([InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='product_back')])
            products_button.append([InlineKeyboardButton(TEXTS["BTN_BUCKET"][lang],callback_data='bucket_view')])

            category=db.get_one_category(product['category_id'])


            await context.bot.delete_message(chat_id=user.id,message_id=message_id)

            await update.callback_query.message.reply_photo(photo=open(category['photo'],'rb'),
                                                            caption=category['name'],
                                                            reply_markup=InlineKeyboardMarkup(products_button))

        elif data[1]=='back':
            product=db.get_one_product(int(data[2]))
            products=db.get_all_product(product['category_id'])
            products_button=[]
            temp_button=[]


            for product in products:
                temp_button.append(InlineKeyboardButton(text=product['name'],
                                                        callback_data=f"product_{product['id']}"))
                if len(temp_button)==2:
                    products_button.append(temp_button)
                    temp_button=[]
            if len(temp_button)>=1:
                products_button.append(temp_button)

            


            products_button.append([InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='product_back')])

            category=db.get_one_category(product['category_id'])


            await context.bot.delete_message(chat_id=user.id,message_id=message_id)

            await update.callback_query.message.reply_photo(photo=open(category['photo'],'rb'),
                                                            caption=category['name'],
                                                            reply_markup=InlineKeyboardMarkup(products_button))
        elif data[1]=='view':
            items=db.get_bucket_items(user_data['id'])
            bucket_buttons=[
                [
                    InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='product_back'),
                    InlineKeyboardButton(TEXTS[ "BTN_ORDER"][lang],callback_data='order')
                ],
                [
                    InlineKeyboardButton(TEXTS["BTN_CLEAR_BUCKET"][lang],callback_data='bucket_clear')
                ]
            ]

            bucket_text='Savatchada\n\n'
            summa=0
            for item in items:
                summa+=item['product_price'] * item['count']
                bucket_text+=f"{item['count']} ✖️ {item['product_name']}\n"

                bucket_buttons.append([
                    InlineKeyboardButton("➖",callback_data=f"bucket_bucket_minus_{item['product_id']}_{item['bucket_id']}"),
                    InlineKeyboardButton(item['product_name'],callback_data="co"),
                    InlineKeyboardButton("➕",callback_data=f"bucket_bucket_plus_{item['product_id']}_{item['bucket_id']}")
                ])
            bucket_text+=f"\nMahsulotlar: {summa} sum"

            await context.bot.delete_message(chat_id=user.id,message_id=message_id)
            await update.callback_query.message.reply_text(bucket_text,
                                                           reply_markup=InlineKeyboardMarkup(bucket_buttons))
            
        elif data[1]=='bucket':
            if data[2]=='plus':
                db.create_or_update_bucket_item(int(data[3]),1,int(data[4]))
                items=db.get_bucket_items(user_data['id'])
                bucket_buttons=[
                    [
                        InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='product_back'),
                        InlineKeyboardButton(TEXTS[ "BTN_ORDER"][lang],callback_data='order')
                    ],
                    [
                        InlineKeyboardButton(TEXTS["BTN_CLEAR_BUCKET"][lang],callback_data='bucket_clear')
                    ]
                ]

                bucket_text='Savatchada\n\n'
                summa=0
                for item in items:
                    summa+=item['product_price'] * item['count']
                    bucket_text+=f"{item['count']} ✖️ {item['product_name']}\n"

                    bucket_buttons.append([
                        InlineKeyboardButton("➖",callback_data=f"bucket_bucket_minus_{item['product_id']}_{item['bucket_id']}"),
                        InlineKeyboardButton(item['product_name'],callback_data="co"),
                        InlineKeyboardButton("➕",callback_data=f"bucket_bucket_plus_{item['product_id']}_{item['bucket_id']}")
                    ])
                bucket_text+=f"\nMahsulotlar: {summa} sum"

                
                # await update.callback_query.message.reply_text(bucket_text,
                #                                             reply_markup=InlineKeyboardMarkup(bucket_buttons))
                

                await update.callback_query.message.edit_text(bucket_text,reply_markup=InlineKeyboardMarkup(bucket_buttons))


            elif data[2]=='minus':
                db.create_or_update_bucket_item(int(data[3]),-1,int(data[4]))
                items=db.get_bucket_items(user_data['id'])
                bucket_buttons=[
                    [
                        InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='product_back'),
                        InlineKeyboardButton(TEXTS[ "BTN_ORDER"][lang],callback_data='order')
                    ],
                    [
                        InlineKeyboardButton(TEXTS["BTN_CLEAR_BUCKET"][lang],callback_data='bucket_clear')
                    ]
                ]

                bucket_text='Savatchada\n\n'
                summa=0
                for item in items:
                    summa+=item['product_price'] * item['count']
                    bucket_text+=f"{item['count']} ✖️ {item['product_name']}\n"

                    bucket_buttons.append([
                        InlineKeyboardButton("➖",callback_data=f"bucket_bucket_minus_{item['product_id']}_{item['bucket_id']}"),
                        InlineKeyboardButton(item['product_name'],callback_data="co"),
                        InlineKeyboardButton("➕",callback_data=f"bucket_bucket_plus_{item['product_id']}_{item['bucket_id']}")
                    ])
                bucket_text+=f"\nMahsulotlar: {summa} sum"

                await update.callback_query.message.edit_text(bucket_text,reply_markup=InlineKeyboardMarkup(bucket_buttons))

                # await update.callback_query.message.reply_text(bucket_text,
                #                                             reply_markup=InlineKeyboardMarkup(bucket_buttons))

        elif data[1]=='clear':
            db.clear_bucket(user_data['id'])
            buttons=[
                [KeyboardButton(TEXTS["BTN_ORDER"][user_data['lang']]),
                KeyboardButton(TEXTS["BTN_MY_ORDER"][user_data['lang']])],
                [KeyboardButton(TEXTS["BTN_FILIAL"][user_data['lang']])]
            ]
            db.add_state(user_data['id'],4)
            
            await context.bot.delete_message(chat_id=user.id,message_id=message_id)
            await update.callback_query.message.reply_text(TEXTS['TEXT_MAIN_MENYU'][user_data['lang']],
                                            reply_markup=ReplyKeyboardMarkup(buttons,resize_keyboard=True))


    elif data[0]=='order':
        location_button=[
            [
                KeyboardButton(TEXTS["BTN_SEND_LOCATION"][lang],request_location=True)
            ]
        ]
        await context.bot.delete_message(chat_id=user.id,message_id=message_id)
        await update.callback_query.message.reply_text(
            TEXTS["TEXT_LOCATION"][lang],
            reply_markup=ReplyKeyboardMarkup(location_button,resize_keyboard=True)
        )


    elif data[0]=='main':
        buttons=[
                [KeyboardButton(TEXTS["BTN_ORDER"][user_data['lang']]),
                KeyboardButton(TEXTS["BTN_MY_ORDER"][user_data['lang']])],
                [KeyboardButton(TEXTS["BTN_FILIAL"][user_data['lang']])]
            ]
        db.add_state(user_data['id'],4)
        await context.bot.delete_message(chat_id=user.id,message_id=message_id)
        await update.callback_query.message.reply_text(TEXTS['TEXT_MAIN_MENYU'][user_data['lang']],
                                                reply_markup=ReplyKeyboardMarkup(buttons,resize_keyboard=True))




            

async def message_hendler(update,context):
    user=update.message.from_user
    text=update.message.text
    user_data=db.get_user(user.id)
    state=db.get_state(user_data['id'])
    lang=user_data['lang']
    
    message_id=update.message.message_id

    if state['state']==2:
        user_data=db.update_user(user_data['id'],name=text)

        button=[
            [KeyboardButton(TEXTS["BTN_PHONE_NUMBER"][lang],request_contact=True)]
        ]
        db.add_state(user_data['id'],3)
        await update.message.reply_text(TEXTS["TEXT_PHONE_NUMBER"][lang],reply_markup=ReplyKeyboardMarkup(button,resize_keyboard=True))

    elif state['state']==4:
        if text==TEXTS["BTN_ORDER"][lang]:
            categories=db.get_all_caregory()
            
            category_button=[]
            temp_button=[]

            for category in categories:
                temp_button.append(InlineKeyboardButton(text=category['name'],callback_data=f"category_{category['id']}"))

                if len(temp_button)==2:
                    category_button.append(temp_button)
                    temp_button=[]

            if len(temp_button)>=1:
                category_button.append(temp_button)

            await update.message.reply_text(TEXTS["START_AN_ORDER"][lang],
                                            reply_markup=ReplyKeyboardMarkup([
                                                [KeyboardButton(TEXTS["MAIN_MENYU_TEXT"][lang])]
                                            ],resize_keyboard=True))

            await update.message.reply_text(f"{TEXTS['CATEGORY_SECTION'][lang]}<a href='https://telegra.ph/Taomnoma-09-30'>.</a>",
                                            reply_markup=InlineKeyboardMarkup(category_button),parse_mode="HTML")
        elif text==TEXTS["BTN_MY_ORDER"][lang]:

            orders=db.get_my_order(user_data['id'])
            if orders:
                for order in orders:
                    summa=0
                    text=f"""Buyurtma raqami: {order['order_id']}\nManzil: {order["location"]}\n\n"""
                    for item in order['items']:
                        item_data=db.get_order_item(item)
                        summa+=item_data['count'] * item_data['product_price']
                        text+=f"{item_data['product_name']}\n{item_data['count']} ✖️ {item_data['product_price']}\n"
                    text+=f"\nBuyurtma vaqti: {order['create_date'].strftime('%d/%m/%Y %H:%M')}"
                    text+=f"\nUmumiy narx:{summa} sum"
                    
                    
                    await update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup([
                                                    [KeyboardButton(TEXTS["MAIN_MENYU_TEXT"][lang])]
                                                ],resize_keyboard=True))

            else:
                await update.message.reply_text("Sizda hozircha hech qanday buyurtma yuq")




            pass
        elif text==TEXTS["BTN_FILIAL"][lang]:
            filial_buttons=[
                [InlineKeyboardButton("ALi-Bobo",callback_data='filial_1'),
                InlineKeyboardButton("Zvezda",callback_data='filial_2')],
                [InlineKeyboardButton(TEXTS["BTN_BACK"][lang],callback_data='main_back')]
            ]
            await context.bot.delete_message(chat_id=user.id,message_id=message_id)
            await update.message.reply_text(f"Filiallarimiz <a href='\https://www.yandex.ru/images/search?from=tabbar&img_url=https%3A%2F%2Fwww.internetworld.de%2Fimg%2F7%2F4%2F1%2F6%2F6%2F2%2FLocal-SEO.tif&lr=35&p=1&pos=12&rpt=simage&text=foto%20filial%20location'>:</a>",
                                            reply_markup=InlineKeyboardMarkup(filial_buttons),parse_mode="HTML")
            

        elif text==TEXTS["MAIN_MENYU_TEXT"][lang]:
            db.clear_bucket(user_data['id']) 
            buttons=[
                [KeyboardButton(TEXTS["BTN_ORDER"][user_data['lang']]),
                KeyboardButton(TEXTS["BTN_MY_ORDER"][user_data['lang']])],
                [KeyboardButton(TEXTS["BTN_FILIAL"][user_data['lang']])]
                    ]
            db.add_state(user_data['id'],4)
            await context.bot.delete_message(chat_id=user.id,message_id=message_id)
            await update.message.reply_text(TEXTS['TEXT_MAIN_MENYU'][user_data['lang']],
                                            reply_markup=ReplyKeyboardMarkup(buttons,resize_keyboard=True))








async def contact_handler(update,context):
    user=update.message.from_user
    user_data=db.get_user(user.id)
    lang=user_data['lang']
    contact=update.message.contact.phone_number
    db.update_user(user_data['id'], phone_number=contact)

    buttons=[
        [KeyboardButton(TEXTS["BTN_ORDER"][lang]),
         KeyboardButton(TEXTS["BTN_MY_ORDER"][lang])],
        [KeyboardButton(TEXTS["BTN_FILIAL"][lang])]
    ]
    db.add_state(user_data['id'],4)
    await update.message.reply_text(TEXTS['TEXT_MAIN_MENYU'][lang],
                                    reply_markup=ReplyKeyboardMarkup(buttons,resize_keyboard=True))



async def location_hendler(update,context):
    lat=update.message.location.latitude
    lon=update.message.location.longitude
    user=update.message.from_user
    user_data=db.get_user(user.id)
    lang=user_data['lang']
    geolacator=Nominatim(user_agent="python_telegram_bot")
    location1=geolacator.reverse(f"{lat},{lon}")
    # # print(lat,lon,user)
    order=db.create_order(user_data['id'],f"{location1}")
    bucket_items=db.get_bucket_items(user_data['id'])
    order_text=''
    for item in bucket_items:
        order_text+=f"{item['count']} ✖️ {item['product_name']}\n"
        db.create_order_item(item['product_id'],item['count'],order["order_id"])
    db.clear_bucket(user_data['id'])
    generited_text=TEXTS["TEXT_CONIFORM_ORDER"][lang]+"\n\n"+ order_text 

    await update.message.reply_text(generited_text)

    buttons=[
                [KeyboardButton(TEXTS["BTN_ORDER"][user_data['lang']]),
                KeyboardButton(TEXTS["BTN_MY_ORDER"][user_data['lang']])],
                [KeyboardButton(TEXTS["BTN_FILIAL"][user_data['lang']])]
            ]
    db.add_state(user_data['id'],4)
    await update.message.reply_text(TEXTS['TEXT_MAIN_MENYU'][user_data['lang']],
                                            reply_markup=ReplyKeyboardMarkup(buttons,resize_keyboard=True))




app=ApplicationBuilder().token("6694251538:AAGZr3bYzUvMb5Xue5uqo0Ndr2Ng3iZDERQ").build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(query_handler))
app.add_handler(MessageHandler(filters.TEXT,message_hendler))
app.add_handler(MessageHandler(filters.CONTACT,contact_handler))
app.add_handler(MessageHandler(filters.LOCATION,location_hendler))



app.run_polling()