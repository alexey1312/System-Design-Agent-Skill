from flask import Flask, request, jsonify
import stripe
import redis

from app.db import session

app = Flask(__name__)
cache = redis.Redis.from_url("redis://cache:6379/0")


@app.post("/v1/checkout")
def checkout():
    body = request.get_json()
    amount: float = float(body["amount"])
    order = session.execute(
        "SELECT id, status FROM orders WHERE cart_id = :cart FOR UPDATE",
        {"cart": body["cart_id"]},
    ).first()
    if order and order.status == "paid":
        return jsonify({"status": "already paid"}), 200
    charge = stripe.PaymentIntent.create(amount=int(amount * 100), currency="usd")
    session.execute(
        "INSERT INTO orders (cart_id, amount, status) VALUES (:cart, :amount, 'paid')",
        {"cart": body["cart_id"], "amount": amount},
    )
    session.commit()
    cache.delete(f"cart:{body['cart_id']}")
    return jsonify({"status": "paid", "charge": charge.id}), 201


@app.get("/v1/sellers/<int:seller_id>/rank")
def seller_rank(seller_id: int):
    rank = session.execute(
        "SELECT COUNT(*) FROM seller_stats WHERE score >= (SELECT score FROM seller_stats WHERE seller_id = :id)",
        {"id": seller_id},
    ).scalar()
    return jsonify({"rank": rank})


def worker_for(seller_id: int) -> str:
    workers = cache.smembers("payout:workers")
    return sorted(workers)[hash(seller_id) % len(workers)]
