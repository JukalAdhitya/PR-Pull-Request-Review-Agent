# In-memory user storage (no database required)
_users = []
_next_id = 1

class User:
    def __init__(self, username, email, user_id=None):
        global _next_id
        self.id = user_id if user_id else _next_id
        if not user_id:
            _next_id += 1
        self.username = username
        self.email = email

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

    @staticmethod
    def get_all():
        return _users.copy()

    @staticmethod
    def get_by_id(user_id):
        for user in _users:
            if user.id == user_id:
                return user
        return None

    @staticmethod
    def create(username, email):
        user = User(username, email)
        _users.append(user)
        return user

    @staticmethod
    def update(user_id, username=None, email=None):
        user = User.get_by_id(user_id)
        if user:
            if username is not None:
                user.username = username
            if email is not None:
                user.email = email
        return user

    @staticmethod
    def delete(user_id):
        global _users
        _users = [user for user in _users if user.id != user_id]
