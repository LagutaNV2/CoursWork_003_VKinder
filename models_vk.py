import configparser
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, session

Base = declarative_base()

config = configparser.ConfigParser()
config.read('setting.ini')
DSN = config["PSQL"]["DSN"]

engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)


class Bot_guests(Base):
    __tablename__ = "bot_guests"
    id = sq.Column(sq.Integer, primary_key=True)
    guest_vk_id = sq.Column(sq.Integer, nullable=False, unique=True)

    def __str__(self):
        return f'guest: {self.id}: {self.guest_vk_id}'


class VK_users(Base):
    __tablename__ = "vk_users"
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, nullable=False, unique=True)
    first_name = sq.Column(sq.String(length=55))
    last_name = sq.Column(sq.String(length=55))
    birth_year = sq.Column(sq.Integer)
    sq.CheckConstraint("1950<=birth_year<=2010")
    city = sq.Column(sq.String(length=80))
    # sex = sq.Column(sq.Integer)
    # sq.CheckConstraint("sex in (0, 1, 2,)")
    link = sq.Column(sq.String(length=255))
    # in_relation = sq.Column(sq.Integer)
    # sq.CheckConstraint("0<=in_relation<=8")
    photo_1 = sq.Column(sq.Text)
    photo_2 = sq.Column(sq.Text)
    photo_3 = sq.Column(sq.Text)
    
    def __str__(self):
        return f'user: {self.vk_id}: ({self.first_name}, {self.last_name}, {self.link}, {self.photo_1}, {self.photo_2}, {self.photo_3})'


class Guest_vk_users(Base):
    __tablename__ = "guest_vk_users"
    id = sq.Column(sq.Integer, primary_key=True)
    guest_id = sq.Column(sq.Integer, sq.ForeignKey("bot_guests.id", ondelete='CASCADE'), nullable=False)
    vk_user_id = sq.Column(sq.Integer, sq.ForeignKey("vk_users.id", ondelete='CASCADE'), nullable=False)
    like = sq.Column(sq.Boolean)
    # blacklist = sq.Column(sq.Boolean)

    bot_guests = relationship(Bot_guests, cascade='save-update, merge, delete',
        passive_deletes=True, backref="guest_vk_users")
    vk_users = relationship(VK_users, cascade='save-update, merge, delete',
        passive_deletes=True, backref="guest_vk_users")

    def __str__(self):
        return f'guest_vk_users: {self.id}: (guest_id - {self.guest_id}, vk_user_id - {self.vk_user_id}, like - {self.like}, dislike - {self.blacklist})'


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # # добавляем id владельца бота
    # guest01 = Bot_guests(guest_vk_id=257332170)
    # session.add_all([guest01])
    # session.commit()


def start_session_postgres():
    engine = sq.create_engine(DSN)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, session

if __name__ == '__main__':
    # создание БД
    engine, session = start_session_postgres()
    create_tables(engine)
    session.close()
