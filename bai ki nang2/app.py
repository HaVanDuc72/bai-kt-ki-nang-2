import sqlite3
import os

from functools import wraps

from flask import Flask, render_template, request, redirect, session

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


app = Flask(__name__)
app.secret_key = "smart-canteen-secret-key"
DATABASE = "database/canteen.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")

        if session.get("role") != "admin":
            return "Bạn không có quyền thực hiện chức năng này!", 403

        return f(*args, **kwargs)

    return decorated_function
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Đang bán'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            min_quantity REAL DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER,
            quantity INTEGER NOT NULL,
            total REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (food_id) REFERENCES foods(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER,
            customer_name TEXT,
            rating INTEGER,
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (food_id) REFERENCES foods(id)
        )
    """)

    # Bảng tài khoản người dùng
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Dữ liệu món ăn mẫu
    count = conn.execute(
        "SELECT COUNT(*) FROM foods"
    ).fetchone()[0]

    if count == 0:
        conn.executemany("""
            INSERT INTO foods
            (name, category, price, quantity, status)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("Cơm gà", "Cơm", 30000, 50, "Đang bán"),
            ("Phở bò", "Món nước", 35000, 40, "Đang bán"),
            ("Mì xào", "Mì", 25000, 35, "Đang bán"),
            ("Trà sữa", "Đồ uống", 20000, 60, "Đang bán"),
            ("Bánh mì", "Đồ ăn nhanh", 15000, 45, "Đang bán")
        ])

    # Dữ liệu nguyên liệu mẫu
    ingredient_count = conn.execute(
        "SELECT COUNT(*) FROM ingredients"
    ).fetchone()[0]

    if ingredient_count == 0:
        conn.executemany("""
            INSERT INTO ingredients
            (name, unit, quantity, min_quantity)
            VALUES (?, ?, ?, ?)
        """, [
            ("Thịt gà", "kg", 4, 10),
            ("Thịt bò", "kg", 12, 8),
            ("Rau xanh", "kg", 3, 8),
            ("Trứng", "quả", 25, 30),
            ("Gạo", "kg", 50, 20)
        ])

    # Tài khoản mẫu
    user_count = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    if user_count == 0:
        conn.executemany("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, [
            ("admin", "123456", "admin"),
            ("nhanvien", "123456", "staff")
        ])

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template(
                "login.html",
                error="Vui lòng nhập tài khoản và mật khẩu!"
            )

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ? AND password = ?
        """, (
            username,
            password
        )).fetchone()

        conn.close()

        if user is None:
            return render_template(
                "login.html",
                error="Tài khoản hoặc mật khẩu không đúng!"
            )

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        return redirect("/dashboard")

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()

    food_count = conn.execute(
        "SELECT COUNT(*) FROM foods"
    ).fetchone()[0]

    ingredient_count = conn.execute(
        "SELECT COUNT(*) FROM ingredients"
    ).fetchone()[0]

    supplier_count = conn.execute(
        "SELECT COUNT(*) FROM suppliers"
    ).fetchone()[0]

    sale_count = conn.execute(
        "SELECT COUNT(*) FROM sales"
    ).fetchone()[0]

    revenue = conn.execute(
        "SELECT COALESCE(SUM(total), 0) FROM sales"
    ).fetchone()[0]

    low_ingredients = conn.execute("""
        SELECT *
        FROM ingredients
        WHERE quantity <= min_quantity
        ORDER BY quantity ASC
    """).fetchall()

    best_selling = conn.execute("""
        SELECT
            foods.name,
            SUM(sales.quantity) AS total_sold
        FROM sales
        JOIN foods ON sales.food_id = foods.id
        GROUP BY sales.food_id
        ORDER BY total_sold DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        food_count=food_count,
        ingredient_count=ingredient_count,
        supplier_count=supplier_count,
        sale_count=sale_count,
        revenue=revenue,
        low_ingredients=low_ingredients,
        best_selling=best_selling
    )


@app.route("/foods")
@login_required
def foods():
    keyword = request.args.get("keyword", "").strip()

    conn = get_db()

    if keyword:
        foods = conn.execute("""
            SELECT * FROM foods
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY id DESC
        """, (f"%{keyword}%", f"%{keyword}%")).fetchall()
    else:
        foods = conn.execute("""
            SELECT * FROM foods
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template(
    "foods.html",
    foods=foods,
    keyword=keyword,
    role=session.get("role")
)


@app.route("/foods/add", methods=["GET", "POST"])
@admin_required
def add_food():

    if request.method == "GET":
        return render_template("food_add.html")

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()
    quantity = request.form.get("quantity", "0").strip()

    if not name or not category or not price:
        return "Vui lòng nhập đầy đủ thông tin!", 400

    try:
        price = float(price)
        quantity = int(quantity)
    except ValueError:
        return "Giá hoặc số lượng không hợp lệ!", 400

    if price < 0 or quantity < 0:
        return "Giá và số lượng không được âm!", 400

    conn = get_db()

    conn.execute("""
        INSERT INTO foods
        (name, category, price, quantity, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        category,
        price,
        quantity,
        "Đang bán"
    ))

    conn.commit()
    conn.close()

    return redirect("/foods")


@app.route("/foods/delete/<int:food_id>", methods=["POST"])
@admin_required
def delete_food(food_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM foods WHERE id = ?",
        (food_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/foods")
@app.route("/foods/edit/<int:food_id>", methods=["GET", "POST"])
@admin_required
def edit_food(food_id):
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "0").strip()
        status = request.form.get("status", "Đang bán").strip()

        if not name or not category or not price:
            conn.close()
            return "Vui lòng nhập đầy đủ thông tin!", 400

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            conn.close()
            return "Giá hoặc số lượng không hợp lệ!", 400

        if price < 0 or quantity < 0:
            conn.close()
            return "Giá và số lượng không được âm!", 400

        conn.execute("""
            UPDATE foods
            SET name = ?,
                category = ?,
                price = ?,
                quantity = ?,
                status = ?
            WHERE id = ?
        """, (
            name,
            category,
            price,
            quantity,
            status,
            food_id
        ))

        conn.commit()
        conn.close()

        return redirect("/foods")

    food = conn.execute(
        "SELECT * FROM foods WHERE id = ?",
        (food_id,)
    ).fetchone()

    conn.close()

    if food is None:
        return "Không tìm thấy món ăn!", 404

    return render_template("edit_food.html", food=food)    


@app.route("/ingredients")
@login_required
def ingredients():
    keyword = request.args.get("keyword", "").strip()

    conn = get_db()

    if keyword:
        ingredients = conn.execute("""
            SELECT * FROM ingredients
            WHERE name LIKE ? OR unit LIKE ?
            ORDER BY id DESC
        """, (f"%{keyword}%", f"%{keyword}%")).fetchall()
    else:
        ingredients = conn.execute("""
            SELECT * FROM ingredients
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template(
        "ingredients.html",
        ingredients=ingredients,
        keyword=keyword,
        role=session.get("role")
    )
@app.route("/ingredients/add", methods=["POST"])
@admin_required
def add_ingredient():
    name = request.form.get("name", "").strip()
    unit = request.form.get("unit", "").strip()
    quantity = request.form.get("quantity", "0").strip()
    min_quantity = request.form.get("min_quantity", "0").strip()

    if not name or not unit:
        return "Vui lòng nhập đầy đủ thông tin!", 400

    try:
        quantity = float(quantity)
        min_quantity = float(min_quantity)
    except ValueError:
        return "Số lượng không hợp lệ!", 400

    if quantity < 0 or min_quantity < 0:
        return "Số lượng không được âm!", 400

    conn = get_db()

    conn.execute("""
        INSERT INTO ingredients
        (name, unit, quantity, min_quantity)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        unit,
        quantity,
        min_quantity
    ))

    conn.commit()
    conn.close()

    return redirect("/ingredients")   
@app.route("/ingredients/delete/<int:ingredient_id>", methods=["POST"])
@admin_required
def delete_ingredient(ingredient_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM ingredients WHERE id = ?",
        (ingredient_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/ingredients")
@app.route("/ingredients/edit/<int:ingredient_id>", methods=["GET", "POST"])
@admin_required
def edit_ingredient(ingredient_id):
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        unit = request.form.get("unit", "").strip()
        quantity = request.form.get("quantity", "0").strip()
        min_quantity = request.form.get("min_quantity", "0").strip()

        if not name or not unit:
            conn.close()
            return "Vui lòng nhập đầy đủ thông tin!", 400

        try:
            quantity = float(quantity)
            min_quantity = float(min_quantity)
        except ValueError:
            conn.close()
            return "Số lượng không hợp lệ!", 400

        if quantity < 0 or min_quantity < 0:
            conn.close()
            return "Số lượng không được âm!", 400

        conn.execute("""
            UPDATE ingredients
            SET name = ?,
                unit = ?,
                quantity = ?,
                min_quantity = ?
            WHERE id = ?
        """, (
            name,
            unit,
            quantity,
            min_quantity,
            ingredient_id
        ))

        conn.commit()
        conn.close()

        return redirect("/ingredients")

    ingredient = conn.execute(
        "SELECT * FROM ingredients WHERE id = ?",
        (ingredient_id,)
    ).fetchone()

    conn.close()

    if ingredient is None:
        return "Không tìm thấy nguyên liệu!", 404

    return render_template(
        "edit_ingredient.html",
        ingredient=ingredient
    ) 


@app.route("/suppliers")
@login_required
def suppliers():
    keyword = request.args.get("keyword", "").strip()

    conn = get_db()

    if keyword:
        suppliers = conn.execute("""
            SELECT * FROM suppliers
            WHERE name LIKE ?
               OR phone LIKE ?
               OR address LIKE ?
            ORDER BY id DESC
        """, (
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%"
        )).fetchall()
    else:
        suppliers = conn.execute("""
            SELECT * FROM suppliers
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template(
        "suppliers.html",
        suppliers=suppliers,
        keyword=keyword,
        role=session.get("role")
    )


@app.route("/suppliers/add", methods=["POST"])
@admin_required
def add_supplier():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    if not name:
        return "Vui lòng nhập tên nhà cung cấp!", 400

    conn = get_db()

    conn.execute("""
        INSERT INTO suppliers (name, phone, address)
        VALUES (?, ?, ?)
    """, (
        name,
        phone,
        address
    ))

    conn.commit()
    conn.close()

    return redirect("/suppliers")
@app.route("/suppliers/delete/<int:supplier_id>", methods=["POST"])
@admin_required
def delete_supplier(supplier_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM suppliers WHERE id = ?",
        (supplier_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/suppliers")
@app.route("/suppliers/edit/<int:supplier_id>", methods=["GET", "POST"])
@admin_required
def edit_supplier(supplier_id):
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name:
            conn.close()
            return "Vui lòng nhập tên nhà cung cấp!", 400

        conn.execute("""
            UPDATE suppliers
            SET name = ?,
                phone = ?,
                address = ?
            WHERE id = ?
        """, (
            name,
            phone,
            address,
            supplier_id
        ))

        conn.commit()
        conn.close()

        return redirect("/suppliers")

    supplier = conn.execute(
        "SELECT * FROM suppliers WHERE id = ?",
        (supplier_id,)
    ).fetchone()

    conn.close()

    if supplier is None:
        return "Không tìm thấy nhà cung cấp!", 404

    return render_template(
        "edit_supplier.html",
        supplier=supplier
    )


@app.route("/sales")
@login_required
def sales():
    keyword = request.args.get("keyword", "").strip()

    conn = get_db()

    if keyword:
        sales = conn.execute("""
            SELECT 
                sales.id,
                foods.name AS food_name,
                sales.quantity,
                sales.total,
                sales.sale_date
            FROM sales
            LEFT JOIN foods ON sales.food_id = foods.id
            WHERE foods.name LIKE ?
            ORDER BY sales.id DESC
        """, (f"%{keyword}%",)).fetchall()
    else:
        sales = conn.execute("""
            SELECT 
                sales.id,
                foods.name AS food_name,
                sales.quantity,
                sales.total,
                sales.sale_date
            FROM sales
            LEFT JOIN foods ON sales.food_id = foods.id
            ORDER BY sales.id DESC
        """).fetchall()

    foods = conn.execute("""
        SELECT * FROM foods
        WHERE status = 'Đang bán'
        ORDER BY name
    """).fetchall()

    conn.close()

    return render_template(
        "sales.html",
        sales=sales,
        foods=foods,
        keyword=keyword
    )
@app.route("/sales/add", methods=["POST"])
@login_required
def add_sale():
    food_id = request.form.get("food_id", "").strip()
    quantity = request.form.get("quantity", "").strip()

    if not food_id or not quantity:
        return "Vui lòng nhập đầy đủ thông tin!", 400

    try:
        food_id = int(food_id)
        quantity = int(quantity)
    except ValueError:
        return "Dữ liệu không hợp lệ!", 400

    if quantity <= 0:
        return "Số lượng phải lớn hơn 0!", 400

    conn = get_db()

    food = conn.execute(
        "SELECT * FROM foods WHERE id = ?",
        (food_id,)
    ).fetchone()

    if food is None:
        conn.close()
        return "Không tìm thấy món ăn!", 404

    if quantity > food["quantity"]:
        conn.close()
        return "Số lượng bán vượt quá số lượng món ăn hiện có!", 400

    total = food["price"] * quantity

    conn.execute("""
        INSERT INTO sales
        (food_id, quantity, total, sale_date)
        VALUES (?, ?, ?, datetime('now', 'localtime'))
    """, (
        food_id,
        quantity,
        total
    ))

    conn.execute("""
        UPDATE foods
        SET quantity = quantity - ?
        WHERE id = ?
    """, (
        quantity,
        food_id
    ))

    conn.commit()
    conn.close()

    return redirect("/sales")
@app.route("/sales/delete/<int:sale_id>", methods=["POST"])
@admin_required
def delete_sale(sale_id):
    conn = get_db()

    sale = conn.execute(
        "SELECT * FROM sales WHERE id = ?",
        (sale_id,)
    ).fetchone()

    if sale is None:
        conn.close()
        return "Không tìm thấy giao dịch!", 404

    conn.execute(
        "UPDATE foods SET quantity = quantity + ? WHERE id = ?",
        (sale["quantity"], sale["food_id"])
    )

    conn.execute(
        "DELETE FROM sales WHERE id = ?",
        (sale_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/sales")


@app.route("/feedback")
@login_required
def feedback():
    conn = get_db()

    feedbacks = conn.execute("""
        SELECT
            feedback.id,
            foods.name AS food_name,
            feedback.customer_name,
            feedback.rating,
            feedback.comment,
            feedback.created_at
        FROM feedback
        LEFT JOIN foods ON feedback.food_id = foods.id
        ORDER BY feedback.id DESC
    """).fetchall()

    foods = conn.execute("""
        SELECT * FROM foods
        ORDER BY name
    """).fetchall()

    conn.close()

    return render_template(
        "feedback.html",
        feedbacks=feedbacks,
        foods=foods
    )
@app.route("/feedback/add", methods=["POST"])
@login_required
def add_feedback():
    food_id = request.form.get("food_id", "").strip()
    customer_name = request.form.get("customer_name", "").strip()
    rating = request.form.get("rating", "").strip()
    comment = request.form.get("comment", "").strip()

    if not food_id or not rating or not comment:
        return "Vui lòng nhập đầy đủ thông tin!", 400

    try:
        food_id = int(food_id)
        rating = int(rating)
    except ValueError:
        return "Dữ liệu không hợp lệ!", 400

    if rating < 1 or rating > 5:
        return "Đánh giá phải từ 1 đến 5 sao!", 400

    conn = get_db()

    food = conn.execute(
        "SELECT id FROM foods WHERE id = ?",
        (food_id,)
    ).fetchone()

    if food is None:
        conn.close()
        return "Không tìm thấy món ăn!", 404

    conn.execute("""
        INSERT INTO feedback
        (food_id, customer_name, rating, comment, created_at)
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
    """, (
        food_id,
        customer_name,
        rating,
        comment
    ))

    conn.commit()
    conn.close()

    return redirect("/feedback")
@app.route("/feedback/delete/<int:feedback_id>", methods=["POST"])
@admin_required
def delete_feedback(feedback_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM feedback WHERE id = ?",
        (feedback_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/feedback")


@app.route("/reports")
@login_required
def reports():
    conn = get_db()

    total_revenue = conn.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM sales
    """).fetchone()[0]

    total_sales = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM sales
    """).fetchone()[0]

    transaction_count = conn.execute("""
        SELECT COUNT(*)
        FROM sales
    """).fetchone()[0]

    average_order = conn.execute("""
        SELECT COALESCE(AVG(total), 0)
        FROM sales
    """).fetchone()[0]

    best_selling = conn.execute("""
        SELECT
            foods.name,
            SUM(sales.quantity) AS total_sold,
            SUM(sales.total) AS revenue
        FROM sales
        JOIN foods ON sales.food_id = foods.id
        GROUP BY sales.food_id
        ORDER BY total_sold DESC
        LIMIT 10
    """).fetchall()

    daily_revenue = conn.execute("""
        SELECT
            DATE(sale_date) AS sale_day,
            SUM(total) AS revenue
        FROM sales
        GROUP BY DATE(sale_date)
        ORDER BY sale_day DESC
        LIMIT 7
    """).fetchall()

    low_ingredients = conn.execute("""
        SELECT *
        FROM ingredients
        WHERE quantity <= min_quantity
        ORDER BY quantity ASC
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_revenue=total_revenue,
        total_sales=total_sales,
        transaction_count=transaction_count,
        average_order=average_order,
        best_selling=best_selling,
        daily_revenue=daily_revenue,
        low_ingredients=low_ingredients
    )
@app.route("/ai-recommend")
@login_required
def ai_recommend():

    conn = get_db()

    # Lấy danh sách món ăn
    foods = conn.execute("""
        SELECT id, name, price, quantity, status
        FROM foods
        ORDER BY id DESC
    """).fetchall()

    # Lấy nguyên liệu
    ingredients = conn.execute("""
        SELECT name, quantity, unit, min_quantity
        FROM ingredients
        ORDER BY quantity ASC
    """).fetchall()

    # Thống kê món bán chạy
    sales = conn.execute("""
        SELECT
            foods.name AS food_name,
            SUM(sales.quantity) AS total_quantity
        FROM sales
        JOIN foods ON sales.food_id = foods.id
        GROUP BY sales.food_id
        ORDER BY total_quantity DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    # ==============================
    # TẠO DANH SÁCH ĐỀ XUẤT CƠ BẢN
    # ==============================

    recommendations = []

    for food in foods:

        food_name = food["name"]

        sold = 0

        for sale in sales:
            if sale["food_name"] == food_name:
                sold = sale["total_quantity"]
                break

        if sold >= 5:
            reason = "Món bán chạy, nên ưu tiên đưa vào thực đơn."

        elif sold >= 1:
            reason = "Món có doanh số ổn định, có thể tiếp tục duy trì."

        else:
            reason = "Món chưa có nhiều dữ liệu bán hàng, có thể dùng để đa dạng thực đơn."

        recommendations.append({
            "name": food_name,
            "price": food["price"],
            "sold": sold,
            "reason": reason
        })

    # ==============================
    # GỌI GEMINI AI
    # ==============================

    ai_text = ""

    if client:

        food_data = []

        for food in foods:
            food_data.append({
                "name": food["name"],
                "price": food["price"],
                "quantity": food["quantity"],
                "status": food["status"]
            })

        ingredient_data = []

        for ingredient in ingredients:
            ingredient_data.append({
                "name": ingredient["name"],
                "quantity": ingredient["quantity"],
                "unit": ingredient["unit"],
                "min_quantity": ingredient["min_quantity"]
            })

        sales_data = []

        for sale in sales:
            sales_data.append({
                "food_name": sale["food_name"],
                "total_quantity": sale["total_quantity"]
            })

        prompt = f"""
Bạn là trợ lý AI quản lý căng tin trường học.

Hãy phân tích dữ liệu căng tin dưới đây và đưa ra đề xuất thực đơn
cho ngày tiếp theo.

DANH SÁCH MÓN ĂN:
{food_data}

NGUYÊN LIỆU HIỆN CÓ:
{ingredient_data}

5 MÓN BÁN CHẠY:
{sales_data}

Yêu cầu:

1. Chọn 3-5 món phù hợp để đưa vào thực đơn.
2. Ưu tiên món bán chạy.
3. Không ưu tiên món có nguyên liệu đang ở mức thấp.
4. Giải thích ngắn gọn lý do lựa chọn.
5. Đề xuất món cần hạn chế nếu nguyên liệu không đủ.
6. Đưa ra cảnh báo nếu có nguyên liệu sắp hết.

Trả lời bằng tiếng Việt, trình bày rõ ràng, dễ đọc.
"""

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            ai_text = response.text

        except Exception as e:

            ai_text = (
                "Không thể kết nối Gemini AI lúc này. "
                "Hệ thống vẫn sử dụng dữ liệu bán hàng để đưa ra đề xuất cơ bản."
            )

    else:

        ai_text = (
            "Chưa cấu hình GEMINI_API_KEY. "
            "Hệ thống đang sử dụng chức năng đề xuất cơ bản."
        )

    return render_template(
        "ai_recommend.html",
        recommendations=recommendations,
        ingredients=ingredients,
        ai_text=ai_text
    )
@app.route("/ai-feedback")
@login_required
def ai_feedback():

    conn = get_db()

    feedbacks = conn.execute("""
        SELECT
            feedback.rating,
            feedback.comment,
            feedback.created_at,
            foods.name AS food_name
        FROM feedback
        LEFT JOIN foods
            ON feedback.food_id = foods.id
        ORDER BY feedback.id DESC
    """).fetchall()

    conn.close()

    # ==============================
    # THỐNG KÊ PHẢN HỒI
    # ==============================

    total = len(feedbacks)

    positive = 0
    neutral = 0
    negative = 0

    for feedback in feedbacks:

        rating = feedback["rating"]

        if rating >= 4:
            positive += 1

        elif rating == 3:
            neutral += 1

        else:
            negative += 1

    if total > 0:
        average_rating = sum(
            feedback["rating"] for feedback in feedbacks
        ) / total
    else:
        average_rating = 0

    # ==============================
    # TỔNG HỢP CƠ BẢN
    # ==============================

    if positive > negative:

        summary = (
            "Khách hàng nhìn chung đánh giá tích cực "
            "về các món ăn."
        )

    elif negative > positive:

        summary = (
            "Có nhiều phản hồi chưa tích cực, "
            "nên kiểm tra lại chất lượng món ăn."
        )

    else:

        summary = (
            "Phản hồi của khách hàng khá cân bằng, "
            "cần tiếp tục theo dõi."
        )

    # ==============================
    # GEMINI AI
    # ==============================

    ai_text = ""

    if client and feedbacks:

        feedback_data = []

        for feedback in feedbacks:

            feedback_data.append({
                "food_name": feedback["food_name"],
                "rating": feedback["rating"],
                "comment": feedback["comment"]
            })

        prompt = f"""
Bạn là AI trợ lý quản lý căng tin trường học.

Hãy phân tích các phản hồi của khách hàng dưới đây:

{feedback_data}

Hãy trả lời bằng tiếng Việt và thực hiện:

1. Đánh giá mức độ hài lòng chung.
2. Xác định các món được đánh giá tốt.
3. Xác định các món hoặc vấn đề nhận nhiều phản hồi chưa tốt.
4. Tóm tắt những ý kiến khách hàng thường nhắc đến.
5. Đề xuất 3 giải pháp cải thiện chất lượng phục vụ.
6. Đưa ra kết luận ngắn gọn cho người quản lý.

Không tự bịa dữ liệu.
Chỉ sử dụng thông tin có trong dữ liệu được cung cấp.
"""

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            ai_text = response.text

        except Exception:

            ai_text = (
                "Không thể kết nối Gemini AI. "
                "Hệ thống vẫn hiển thị thống kê phản hồi cơ bản."
            )

    elif not feedbacks:

        ai_text = (
            "Chưa có phản hồi của khách hàng để Gemini AI phân tích."
        )

    else:

        ai_text = (
            "Chưa cấu hình GEMINI_API_KEY. "
            "Hệ thống đang sử dụng thống kê phản hồi cơ bản."
        )

    return render_template(
        "ai_feedback.html",
        feedbacks=feedbacks,
        total=total,
        positive=positive,
        neutral=neutral,
        negative=negative,
        average_rating=average_rating,
        summary=summary,
        ai_text=ai_text
    )
@app.route("/ai-report")
@login_required
def ai_report():

    conn = get_db()

    # ==============================
    # THỐNG KÊ DOANH THU
    # ==============================

    total_revenue = conn.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM sales
    """).fetchone()[0]

    total_quantity = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM sales
    """).fetchone()[0]

    total_orders = conn.execute("""
        SELECT COUNT(*)
        FROM sales
    """).fetchone()[0]

    # ==============================
    # MÓN BÁN CHẠY
    # ==============================

    best_selling = conn.execute("""
        SELECT
            foods.name AS food_name,
            SUM(sales.quantity) AS total_quantity,
            SUM(sales.total) AS revenue
        FROM sales
        JOIN foods
            ON sales.food_id = foods.id
        GROUP BY sales.food_id
        ORDER BY total_quantity DESC
        LIMIT 5
    """).fetchall()

    # ==============================
    # DOANH THU THEO NGÀY
    # ==============================

    daily_revenue = conn.execute("""
        SELECT
            DATE(sale_date) AS sale_day,
            SUM(total) AS revenue,
            SUM(quantity) AS quantity
        FROM sales
        GROUP BY DATE(sale_date)
        ORDER BY sale_day DESC
        LIMIT 7
    """).fetchall()

    conn.close()

    # ==============================
    # GEMINI AI
    # ==============================

    ai_text = ""

    if client:

        best_selling_data = []

        for item in best_selling:

            best_selling_data.append({
                "food_name": item["food_name"],
                "quantity": item["total_quantity"],
                "revenue": item["revenue"]
            })

        daily_data = []

        for item in daily_revenue:

            daily_data.append({
                "date": item["sale_day"],
                "revenue": item["revenue"],
                "quantity": item["quantity"]
            })

        prompt = f"""
Bạn là AI trợ lý phân tích doanh thu cho căng tin trường học.

Dữ liệu kinh doanh:

TỔNG DOANH THU:
{total_revenue:,.0f} VNĐ

TỔNG SỐ PHẦN ĐÃ BÁN:
{total_quantity}

TỔNG SỐ GIAO DỊCH:
{total_orders}

5 MÓN BÁN CHẠY:
{best_selling_data}

DOANH THU 7 NGÀY GẦN NHẤT:
{daily_data}

Hãy tạo báo cáo doanh thu ngắn gọn bằng tiếng Việt.

Yêu cầu:

1. Nêu tổng doanh thu.
2. Nêu tổng số lượng món đã bán.
3. Nêu số giao dịch.
4. Xác định món bán chạy nhất.
5. Phân tích xu hướng doanh thu dựa trên dữ liệu.
6. Đưa ra 3 đề xuất giúp tăng doanh thu.
7. Nếu dữ liệu chưa đủ để kết luận xu hướng thì phải nói rõ.

Không tự bịa dữ liệu.
Chỉ sử dụng số liệu được cung cấp.
Trình bày rõ ràng, dễ đọc.
"""

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            ai_text = response.text

        except Exception:

            ai_text = (
                "Không thể kết nối Gemini AI lúc này. "
                "Vui lòng kiểm tra GEMINI_API_KEY."
            )

    else:

        ai_text = (
            "Chưa cấu hình GEMINI_API_KEY. "
            "Vui lòng cấu hình API Key để sử dụng báo cáo AI."
        )

    return render_template(
        "ai_report.html",
        total_revenue=total_revenue,
        total_quantity=total_quantity,
        total_orders=total_orders,
        best_selling=best_selling, 
        daily_revenue=daily_revenue,
        ai_text=ai_text
    )
if __name__ == "__main__":
    init_db()
    app.run(debug=True)