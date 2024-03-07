import psycopg
from psycopg.rows import dict_row

class DB:
    def __init__(self):
        self.conn=psycopg.connect("dbname=delivery user=postgres password=baxa05",row_factory=dict_row)
        self.conn.execute("""
            create table if not exists "user"(
                id bigserial primary key,
                name varchar(30),
                phone_number varchar(30),
                lang varchar(20),
                tg_firstname varchar(70),
                tg_username varchar(70),
                tg_id bigint,
                joined_date timestamp default now()
            );
                          
            create table if not exists "user_state"(
                user_id integer,
                state integer,
                foreign key(user_id)
                references "user"(id)
            );
                          
            create table if not exists "category"(
                id bigserial primary key,
                name varchar(50),
                photo varchar(100)
            );

            create table if not exists "product" (
                id bigserial primary key,
                name varchar(50),
                photo varchar(100),
                price integer,
                description text,
                category_id integer,
                foreign key(category_id)
                references "category"(id)
            );

            create table if not exists "bucket"(
                bucket_id bigserial primary key,
                user_id integer,
                foreign key(user_id)
                references "user"(id)
            );

            create table if not exists "bucket_item"(
                id bigserial primary key,
                product_id integer,
                count integer,
                bucket_id integer,
                foreign key(product_id)
                references "product"(id),        
                foreign key(bucket_id)
                references "bucket"(bucket_id)         
            );

            create table if not exists "order"(
                order_id bigserial primary key,
                user_id integer,
                location varchar(100),
                foreign key(user_id)
                references "user"(id)
            );    


            create table if not exists "order_item"(
                id bigserial primary key,
                product_id integer,
                count integer,
                order_id integer,
                foreign key(product_id)
                references "product"(id),      
                foreign key(order_id)
                references "order"(order_id)         
            );                       


        """)
        self.conn.commit()



    def add_user(self,tg_id,tg_firstname,tg_username):
        user=self.conn.execute(f"""
            insert into "user"(tg_id,tg_firstname,tg_username)
            values({tg_id},'{tg_firstname}','{tg_username}')
            returning *
        """).fetchone()
        self.conn.commit()
        return user

    def get_user(self,tg_id):
        user=self.conn.execute(f"""
            select * from "user"
            where tg_id={tg_id}
        """).fetchone()
        self.conn.commit()
        return user
        
    



    def add_state(self,user_id,state):
        if self.get_state(user_id):
            state=self.conn.execute(f"""
                update "user_state" set state ={state}
                where user_id={user_id}
                returning state
            """).fetchone()
        else:
            state=self.conn.execute(f"""
                insert into "user_state"
                values({user_id},{state})
                returning state
            """).fetchone()
        self.conn.commit()
        return state

    def get_state(self,user_id):
        state=self.conn.execute(f"""
            select state from "user_state"
            where user_id={user_id}
        """).fetchone()
        return state


    def update_user(self,user_id, **kwargs):
        if kwargs.get('lang'):
            if kwargs['lang']=='1':
                user=self.conn.execute(f"""
                    update "user" set lang ='uzbek'
                    where id={user_id}
                    returning *
                """).fetchone()

            elif kwargs['lang']=='2':
                user=self.conn.execute(f"""
                    update "user" set lang ='russian'
                    where id={user_id}
                    returning *
                """).fetchone()

            else:
                user=self.conn.execute(f"""
                    update "user" set lang ='english'
                    where id={user_id}
                    returning *
                """).fetchone()
            
            self.conn.commit()
            return user

        if kwargs.get('name'):
            user=self.conn.execute(f"""
                    update "user" set name ='{kwargs['name']}'
                    where id={user_id}
                    returning *
                """).fetchone()
            
            self.conn.commit()
            return user

        if kwargs.get('phone_number'):
            user=self.conn.execute(f"""
                    update "user" set  phone_number ='{kwargs['phone_number']}'
                    where id={user_id}
                    returning *
                """).fetchone()
            
            self.conn.commit()
            return user

    

    def get_all_caregory(self):
        categories=self.conn.execute("""
            select * from "category"
        """).fetchall()
        return categories
    

    def get_all_product(self,category_id):
        products=self.conn.execute(f"""
            select * from "product"
            where category_id={category_id}
        """).fetchall()
        return products
    
    def get_one_category(self,category_id):
        category=self.conn.execute(f"""
            select * from "category"
            where id={category_id}
        """).fetchone()
        return category
    

    def get_one_product(self,product_id):
        product=self.conn.execute(f"""
            select * from "product"
            where id = {product_id}
        """).fetchone()
        return product



    def get_or_create_bucket(self,user_id):
        bucket=self.conn.execute(f"""
            select bucket_id from "bucket"
            where user_id={user_id}
        """).fetchone()

        if bucket:
            return bucket
        else:
            bucket=self.conn.execute(f"""
                insert into "bucket"(user_id)
                values({user_id})
                returning bucket_id
                """).fetchone()
            self.conn.commit()
            return bucket
        

    def create_or_update_bucket_item(self,product_id,count,bucket_id):
        bucket_item=self.conn.execute(f"""
            select * from "bucket_item"
            where product_id={product_id} and bucket_id={bucket_id}
        """).fetchone()

        if bucket_item:
            count=bucket_item['count']+count
            self.conn.execute(f"""
                update "bucket_item" set count={count}
                where product_id={product_id} and bucket_id={bucket_id}
            """)

        else:
            self.conn.execute(f"""
                insert into "bucket_item" (product_id,count,bucket_id)
                values({product_id},{count},{bucket_id})
            """)
        self.conn.commit()


    def clear_bucket(self,user_id):
        self.conn.execute(f"""
            delete from "bucket_item"
            where bucket_id in (select bucket_id from "bucket" where user_id={user_id})
        """)

        self.conn.commit()


    def get_bucket_items(self,user_id):
        bucket_items=self.conn.execute(f"""
            select bi.*, p.name as product_name, p.price as product_price
            from "bucket_item" bi
            inner join "bucket" b ON bi.bucket_id=b.bucket_id
            inner join "product" p ON p.id= bi.product_id
            where b.user_id={user_id}
            order by bi.id asc
        """).fetchall()
        return bucket_items


    def create_order(self,user_id,location):
        order=self.conn.execute(f"""
            insert into "order"(user_id,location)
            values({user_id},'{location}')
            returning order_id
        """).fetchone()
        self.conn.commit()
        return order

    def create_order_item(self,product_id,count,order_id):
        self.conn.execute(f"""
            insert into "order_item"(product_id,count,order_id)
            values({product_id},{count},{order_id})
        """)
        self.conn.commit()


    def get_my_order(self,user_id):
        orders=self.conn.execute(f"""
            select o.order_id ,o."location" ,o.create_date,
            array_agg(oi.id) as items 
            from "order" o 
            inner join order_item oi  on oi.order_id =o.order_id 
            where o.user_id ={user_id}
            group by o.order_id 
        """).fetchall()
        return orders
    

    def get_order_item(self,item_id):
        item=self.conn.execute(f"""
            select oi.id,p.name as product_name,oi.count,p.price as product_price
            from order_item oi 
            inner join product p  on oi.product_id =p.id 
            where oi.id={item_id}
        """).fetchone()
        return item















    # def get_state(self,user_id):
        
    #     state=self.conn.execute(f"""
    #         select state from "user_state"
    #         where user_id={user_id}   
    #     """).fetchone()
    #     return state
        
    # def add_state(self,user_id,state):
    #     user=self.get_state(user_id)

    #     if not user:
    #         self.conn.execute(f"""
    #             insert into "user_state"
    #             values({user_id},{state})
    #         """)
    #     else:
    #         self.conn.execute(f"""
    #             update "user_state" set state={state}
    #             where user_id={user_id}
    #         """)
    #     self.conn.commit()
            
            