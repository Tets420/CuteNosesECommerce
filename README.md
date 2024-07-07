# Cute Noses Online Store - apparel and pet essentials
#### Video Demo:  <https://youtu.be/JqoXBVNbnZk>
#### Description:
Cute Noses Online Store will be your one-stop-shop for all things pet-related, offering a wide range of apparel and essentials for your furry companions. The store is designed to provide a seamless and delightful shopping experience, with a user-friendly interface and features tailored to meet the needs of pet owners.

## User facing features-

#### Admin and User Authentication and Authorization:
To ensure a secure and personalized experience, users will be required to register by providing their credentials, including:

* username
* password
* email address (for notification purposes)
* billing address
* shipping address (for delivery purposes)

Once registered users can access their homepage where the shopping grid is already displayed.
On top of the page in the navigation bar are **My Cart**, **My Account**, **Order History**, **Log Out**
The user will also be able to change their password in the **My Account** link


these lines of code at 463-477 automatically registers all as "user"
```
                db.execute(
                "INSERT INTO users (username, hash, email, usercredential, billingAddStreet, billingAddCity, billingAddProvince, billingAddZip, shippingAddStreet, shippingAddCity, shippingAddProvince, shippingAddZip) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?)",
                username,
                hash,
                email,
                "user",
                billing_address["street"],
                billing_address["city"],
                billing_address["province"],
                billing_address["zip"],
                shipping_address["street"],
                shipping_address["city"],
                shipping_address["province"],
                shipping_address["zip"],
            )
```

> [!NOTE]
> to minimize lines of code, admin credentials will be updated on **_cutenoses.db_** by doing UPDATE on the _usercredential_ field into _"admin"_ once registered as a user

The website will automatically route the user or admin to their assigned pages once registered in the database.

#### Homepage and Product Management:

The shopping homepage will display information from the **_products_** table in the database

* Product Image (queried through a url)
* Product name
* Price
* Available Quantity

The products can be filtered on the user homepage with a dropdown filter script (generated with Claude's help)

in index.html (user home shopping page) lines 6-11
```
<select class="form-control" onchange="filterProducts(this.value)">
                <option value="all" {% if selected_category == "all" %}selected{% endif %}>All Categories</option>
                {% for category in categories %}
                <option value="{{ category.categoryID }}" {% if selected_category == category.categoryID|string %} selected {% endif %}>{{ category.name }}</option>
                {% endfor %}
            </select>
```

as well as the ability to add to cart on mouse hover on lines 48-54
```
$('.product-card').hover(function() {
    $(this).find('.add-to-cart-form').show();
    $(this).find('.quantity-input').val(1); // Reset the quantity input value to 1
}, function() {
    $(this).find('.add-to-cart-form').hide();
});
```
and have access to a **virtual cart** that will display their current purchases

* add or remove items
* adjust quantities
* review their selections before proceeding to checkout.

cart items are retrieved by combining our **_shopcart_** and **_products_** tables from our database **_cutenoses.db_**

#### Checkout Process:
The checkout process will be streamlined to provide a hassle-free experience. Users will have the option to pay via cash on delivery or through **GCash, a popular local payment method or a cash on delivery option**. In the future, the store aims to integrate additional online payment APIs to offer more payment options to customers.

> [!NOTE]
> currently undergoing the registration of the e-commerce store in order to get the online payment APIs. to be implemented in the future

checkout route has this line to ensure the confirmation delivers the right address from our database

flask app lines 286-287
```
shipping_address = f"{user_shipping_address[0]['shippingAddStreet']}, {user_shipping_address[0]['shippingAddCity']}, {user_shipping_address[0]['shippingAddProvince']}, {user_shipping_address[0]['shippingAddZip']}"
```

#### Order History:
Customers can easily access their order history, which will display a list of their past purchases, details including

* timestamp of the purchase
* product name
* quantity
* total amount
* order status.

This page will allow users to track their orders in the **_orderStatus_** column and by default when they press checkout it will be inserted to the database as

lines 306-314
```
    for item in cart_items:
        db.execute(
            "INSERT INTO orders (userID, productID, quantity, orderStatus, paymentMethod, totalAmount) VALUES (?, ?, ?, 'CheckOut', ?, ?)",
            user_id,
            item["productID"],
            item["quantity"],
            payment_method,
            total_amount,
        )
```

## Additional Features

#### Admin dashboard:
The admin dashboard will provide a centralized location for administrators to monitor the site's status, access analytics, and manage various aspects of the store's operations. This feature will enable data-driven decision-making and facilitate efficient store management.

In the current version the Admin will have full visibility of the **_products_** and **_orders_** database which will be used for logistics.

Products will show

* Product ID
* Product Name
* Price
* Quantity
* Category ID

Orders will show

* Order ID
* Timestamp of the order
* Customer username
* Product name
* Quantity
* Total Amount
* Order status

> [!NOTE]
> in this version of the cutenoses shop admin will UPDATE **_orderStatus_** in the **_orders_** table

#### Future Enhancements - reviews and social media integration

Additionally, the store plans to explore integrating more payment gateways and developing a dedicated mobile app to provide an even more convenient shopping experience for customers on the go. I am also planning to add a review system and social media integration.


# Ad Majorem Dei Gloriam
