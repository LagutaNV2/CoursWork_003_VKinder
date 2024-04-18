import configparser
import random

import sqlalchemy
import sqlalchemy as sq
from sqlalchemy import update
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, session

import models_vk
from models_vk import Bot_guests, VK_users, Guest_vk_users, start_session_postgres

def get_bot_user(current_vk_id):
    '''выводит id, vk_id для знакомого пользователя или None для нового'''
    engine, session = start_session_postgres()
    selected = session.query(Bot_guests.id, Bot_guests.guest_vk_id)\
        .filter(Bot_guests.guest_vk_id==str(current_vk_id)).scalar()
    session.close()
    print('result check_user: ', selected)
    return selected

def add_user(current_vk_id):
    '''добавление в базу пользователей нового user'''
    engine, session = start_session_postgres()
    user = Bot_guests(guest_vk_id=current_vk_id)
    session.add_all([user])
    session.commit()
    session.close()
    print('added user: vk_id', current_vk_id)

def del_user(current_vk_id):
    '''удаление из базы пользователей бота (текущего USERа)'''
    engine, session = start_session_postgres()
    if get_bot_user(current_vk_id):
        session.query(Bot_guests).filter(Bot_guests.guest_vk_id == current_vk_id).delete()
        session.commit()
        session.close()
        return('Done')
    else:
        print('vk_id не существует')
        session.close()
        return ('Blocked')
 
def add_vk_users(candidat, photo_01, photo_02, photo_03):
    '''запись в базу кандидата, полученного для гостя бота'''
    engine, session = start_session_postgres()
    
    element = VK_users(vk_id=candidat['id'],
                           first_name=candidat['first_name'],
                           last_name=candidat['last_name'],
                           birth_year=candidat['bdate'][-4:],
                           city=candidat['city']['title'],
                           link=f'https://vk.com/id{candidat['id']}',
                           photo_1=photo_01,
                           photo_2=photo_02,
                           photo_3=photo_03)
    session.add_all([element])
    session.commit()
    session.close()

def check_vk_user(current_vk_id):
    '''возвращает None, если user в базе отсутствует'''
    engine, session = start_session_postgres()
    selected = session.query(VK_users.id, VK_users.vk_id) \
        .filter(VK_users.vk_id == str(current_vk_id)).scalar()
    session.close()
    print('result check_vk_user: ', selected)
    return selected

def get_vk_user(pk_vk_user):
    '''возвращает None, если user в базе отсутствует'''
    engine, session = start_session_postgres()
    selected = session.query(VK_users.id, VK_users.vk_id, VK_users.first_name,\
        VK_users.last_name, VK_users.birth_year, VK_users.city, VK_users.link,\
        VK_users.photo_1, VK_users.photo_2, VK_users.photo_3)\
        .filter(VK_users.id == str(pk_vk_user)).all()
    session.close()
    print('result get_vk_user: ', selected)
    return selected

def add_connect_to_db(guest_id, vk_user_id):
    '''создание таблицы связей гостя бота с подборкой кандидатов'''
    engine, session = start_session_postgres()
    element = Guest_vk_users(guest_id=guest_id, vk_user_id=vk_user_id)
    session.add_all([element])
    session.commit()
    session.close()
    
def add_like_to_db(id_, like_):
    ''' like = 1 (good!), like = 0 (send to blacklist), like = None (don't know)'''
    engine, session = start_session_postgres()
    
    session.query(Guest_vk_users).filter(Guest_vk_users.id == id_).update({Guest_vk_users.like:like_}, synchronize_session = False)
    
    session.commit()
    session.close()

def get_personal_list(guest_id):
    '''получаем список кандидатов, найденных для данного пользователя
    в виде списка кортежей: [(pk, id гостя бота в базе, id usera в базе, like)]'''
    engine, session = start_session_postgres()
    select = session.query(Guest_vk_users) \
        .with_entities(Guest_vk_users.id, Guest_vk_users.guest_id, Guest_vk_users.vk_user_id, Guest_vk_users.like) \
        .join(VK_users, VK_users.id == Guest_vk_users.vk_user_id) \
        .filter(Guest_vk_users.guest_id == guest_id).all()
    session.close()
    return select
