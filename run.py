from app import db, create_app, socketio

# db.create_all()
app = create_app()
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=80, cors_allowed_origins="*")
    # application.run(host='0.0.0.0')
