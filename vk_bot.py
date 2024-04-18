import requests
from random import randrange
import json
import configparser
import os

from pprint import pprint

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton

from query_db_vk import get_bot_user, add_user, del_user, add_vk_users, check_vk_user, add_connect_to_db, \
    get_personal_list, get_vk_user, add_like_to_db

# initialization
config = configparser.ConfigParser()
config.read('setting.ini')
bot_token = config["VK"]["bot_token"]
bot_id = config["VK"]["bot_id"]
owner_token = config["VK"]["owner_token"]
owner_id = config["VK"]["owner_id"]


class VK_Client_bot:
    API_BAS_URL = 'https://api.vk.com/method'
    
    def __init__(self, owner_token, owner_id, bot_token, bot_id):
        '''создаем объект бота'''
        self._owner_token = owner_token
        self._owner_id = owner_id
        self._bot_token = bot_token
        self._bot_id = bot_id
        
    def _get_common_params(self):
        return {
            'access_token': self._owner_token,
            'v': '5.199'
        }
    
    def _build_url(self, api_metod):
        return f'{self.API_BAS_URL}/{api_metod}'


class VK_client_bot_guest(VK_Client_bot):
    def __init__(self, owner_token, owner_id, bot_token, bot_id, user_id):
        super().__init__(owner_token, owner_id, bot_token, bot_id)
        self._user_id = user_id
        self._user_name = self.get_user_info()['first_name']
        self._users_search_extend = False
        self._commands = ['привет - приветствие',
                          'help - перечень команд',
                          'delete_me - удалить мой эккаунт, '
                          'next - просмотр кандидатов',
                          'start - запускает поиск',
                          'пока - прощание',
                          'stop - вход из цикла просмотра',
                          'show - просмотр кандидатов']
    
    def get_user_info(self):
        '''получаем информацию о госте бота'''
        params = self._get_common_params()
        params.update({'user_ids': self._user_id,
                       'fields': 'city,sex,bdate,country'})
        response = requests.get(self._build_url('users.get'), params=params)
        users_info = response.json()['response'][0]
        users_info['candidate_sex'] = 1 if users_info['sex'] == 2 else 2
        
        print(f'{users_info=}')
        
        # сохраняем данные в json файл, чтобы видеть структуру
        if not os.path.exists('results'):
            os.mkdir('results')
        file_path = os.path.join(os.getcwd(), f'results/bot_guest_info{self._user_id}.json')
        with open(file_path, 'w', encoding="utf-8") as f:
            json.dump(users_info, f, indent=4, ensure_ascii=False)
        
        return users_info
    
    def get_candidats(self, sex, city_id, year, user_id, count_for_search):
        '''поиск по городу и возрасту
        для формирования первоначального списка кандидатов'''
        age_from = 2024 - int(year) - 1
        age_to = 2024 - int(year) + 2
        params = self._get_common_params()
        params.update({'sort': 0,
                       'count': count_for_search,
                       'has_photo': 1,
                       'fields': 'id,city,sex,bdate,relation',
                       'age_from': age_from,
                       'age_to': age_to,
                       'status': 6,
                       'city': city_id,
                       'sex': sex})
        
        # print(f'{params=}')
        response = requests.get(self._build_url('users.search'), params=params)
        response.encoding = 'utf-8'
        
        # сохраняем данные в json файл, чтобы видеть структуру
        if not os.path.exists('results'):
            os.mkdir('results')
        file_path = os.path.join(os.getcwd(), f'results/candidats_{user_id}.json')
        with open(file_path, 'w', encoding="utf-8") as f:
            json.dump(response.json(), f, indent=4, ensure_ascii=False)
        
        candidats_response = response.json()['response']['items']
        dublies = []
        pprint(f'befor: {len(candidats_response)=}, \n {candidats_response=}')
        
        for user in candidats_response:
       
            print(f'{user['id']=}')
            if 'city' not in list(user):
                user['city'] = {"id": '', "title": ''}
            
            if check_vk_user(user['id']) is None:
                try:
                    photo_01, photo_02, photo_03 = vk_bot._get_candidats_photos(user['id'])
                    add_vk_users(user, photo_01, photo_02, photo_03)
                    
                    pk_bot_guest = get_bot_user(user_id)
                    pk_vk_user = check_vk_user(user['id'])
                    
                    # def add_connect_to_db(guest_id, vk_user_id)-ключи!
                    add_connect_to_db(pk_bot_guest, pk_vk_user)
                except:
                    photo_01, photo_02, photo_03 = None, None, None
                    add_vk_users(user, photo_01, photo_02, photo_03)
                    pk_bot_guest = get_bot_user(user_id)
                    pk_vk_user = check_vk_user(user['id'])
                    add_connect_to_db(pk_bot_guest, pk_vk_user)
                    
            else:
                dublies.append(user)
                print(f'{user['id']=} уже есть в базе ')
        for user_dubl in dublies:
            deleted_user = candidats_response.remove(user_dubl)
            print(f'{deleted_user=}')
        pprint(f'after: {len(candidats_response)=}, \n {candidats_response=}')
        return candidats_response
    
    def get_candidats_extend(self, sex, country, year, user_id, count_for_search):
        '''если поиск по городу не дал результата ищем по стране и с увеличенным возрастом'''
        age_from = 2024 - int(year) - 4
        age_to = 2024 - int(year) + 4
        params = self._get_common_params()
        params.update({'sort': 0,
                       'count': count_for_search,
                       'has_photo': 1,
                       'fields': 'id,city,country,sex,bdate,relation',
                       'age_from': age_from,
                       'age_to': age_to,
                       'status': 6,
                       'country': country,
                       'sex': sex})
        
        response = requests.get(self._build_url('users.search'), params=params)
        response.encoding = 'utf-8'
        
        # сохраняем данные в json файл, чтобы видеть структуру
        if not os.path.exists('results'):
            os.mkdir('results')
        file_path = os.path.join(os.getcwd(), f'results/candidats_{user_id}.json')
        with open(file_path, 'w', encoding="utf-8") as f:
            json.dump(response.json(), f, indent=4, ensure_ascii=False)
        
        candidats_response = response.json()['response']['items']
        dublies = []
        
        for user in candidats_response:
            print(f'{user['id']=}')
            pprint(f'{user=}')
            if 'city' not in list(user):
                user['city'] = {"id": '', "title": ''}
            
            if check_vk_user(user['id']) is None:
                photo_01, photo_02, photo_03 = vk_bot._get_candidats_photos(user['id'])
                add_vk_users(user, photo_01, photo_02, photo_03)
                
                pk_bot_guest = get_bot_user(user_id)
                pk_vk_user = check_vk_user(user['id'])
                
                # def add_connect_to_db(guest_id, vk_user_id)-ключи!
                add_connect_to_db(pk_bot_guest, pk_vk_user)
            
            else:
                dublies.append(user)
                print(f'{user['id']=} уже есть в базе ')
            
        for user_dubl in dublies:
            deleted_user = candidats_response.remove(user_dubl)
            print(f'{deleted_user=}')
        pprint(f'after: {len(candidats_response)=}, \n {candidats_response=}')
        return candidats_response
    
    def _get_candidats_photos(self, candidat_id):
        '''получаем ссылки на фото через два запроса:
        фото профиля и стены, оставляем тот  ответ, где получено больше фотографий'''
        self.candidate_id = candidat_id
        params = self._get_common_params()
        params.update({'owner_id': self.candidate_id,
                       'album_id': 'profile',
                       'extended': 1,
                       })
        
        response = requests.get(self._build_url('photos.get'),
                                params=params)
        user_photos_profile = response.json()['response']['items']
        
        params['album_id'] = 'wall'
        
        response = requests.get(self._build_url('photos.get'),
                                params=params)
        user_photos_wall = response.json()['response']['items']
        
        print(f'{len(user_photos_profile)=} {len(user_photos_wall)=}')
        user_photos = user_photos_profile if len(user_photos_wall) <= len(user_photos_profile) else user_photos_wall
        
        photos = {}
        for photo in user_photos:
            photos.update(
                {photo['likes']['count']: (photo['sizes'][-2]['url'],  # добавлена инфа для вывода фото в сообщ-е
                                           photo['owner_id'],
                                           photo['id'])})
        sort_photos = sorted(photos.items(), reverse=1)
        print(f'{sort_photos=}')
        
        if len(sort_photos) >= 3:
            return (sort_photos[0][1], sort_photos[1][1], sort_photos[2][1])
        elif len(sort_photos) == 2:
            return (sort_photos[0][1], sort_photos[1][1], None)
        elif len(sort_photos) == 1:
            return (sort_photos[0][1], None, None)
        else:
            return (None, None, None)
    
    def _get_describe_of_candidat(self, candidat):
        cand_descript = get_vk_user(candidat[2])
        pprint(cand_descript)
        candidat_id = cand_descript[0][1]
        # вывод фото
        ph1, ph2, ph3 = cand_descript[0][7], cand_descript[0][8], cand_descript[0][9]
        if ph1 is not None and ph1 != '':
            ph1_id = ph1.split(',')[2]
            vk_bot.write_msg_foto(self._user_id, candidat_id, ph1_id, 'фото 1')
        if ph2 is not None and ph2 != '':
            ph2_id = ph2.split(',')[2]
            vk_bot.write_msg_foto(self._user_id, candidat_id, ph2_id, 'фото 2')
        if ph3 is not None and ph3 != '':
            ph3_id = ph3.split(',')[2]
            vk_bot.write_msg_foto(self._user_id, candidat_id, ph3_id, 'фото 3')
        city = cand_descript[0][5]
        link = cand_descript[0][6]
        result = '' + cand_descript[0][2] + ' ' + cand_descript[0][3] + ', ' + str(cand_descript[0][4])
        if city is not None and city != '':
            result = result + ', ' + city
        result = result + ', ссылка: ' + link
        return result
    def new_message(self, message):
        # Привет, Hi
        if 'привет' in message.lower() or 'hi' in message.lower():
            print(f"Вход пользователя {self._user_name}")
            
            user_descript = vk_bot.get_user_info()
            if 'bdate' not in list(user_descript):
                del_user(self._user_id)
                return (f'Привет (čao), {self._user_name}!'
                        f' У тебя не указана дата рождения, '
                        f'т.е. нет информации возрасте. Поиск в данном случае не работает. '
                        f'Можешь исправить настройки профиля и зайти сюда снова. \n'
                        f'Nemate datum rođenja, nema podataka o starosti. Pretraga'
                        f' u ovom slučaju ne radi, možete popraviti podešavanja profila '
                        f'i ponovo otići ovde')
            
            if '.' in user_descript['bdate'][-4:]:
                del_user(self._user_id)
                return (f'Привет (čao), {self._user_name}!'
                        f' У тебя указана дата рождения (Imate datum rođenja): '
                        f'{user_descript['bdate'][-4:]}, '
                        f'т.е. нет информации возрасте. Поиск в данном случае не работает. '
                        f'Можешь исправить настройки профиля и зайти сюда снова. \n'
                        f'nema podataka o starosti. Pretraga u ovom slučaju ne funkcioniše. '
                        f'Možete popraviti podešavanja profila i ponovo otići ovde.')
            
            return (f"Привет (čao), {self._user_name}! Напиши 'start' и я подберу для тебя кандидатов...\n"
                    f"Napiši 'start' i potražiću kandidate za tebe...")
            
        # help
        elif 'help' in message.lower():
            return f'список команд: {self._commands}'
        
        # delete_me
        elif 'delete_me' in message.lower():
            del_user(self._user_id)
            return f"Твой эккаунт удален. Чао, {self._user_name}!"
        
        # next, далее, show
        elif 'next' in message.lower() or 'далее' in message.lower() or 'show' in message.lower():
            # 1 формируем стартовый список кандидатов для нашего гостя
            pk_bot_guest = get_bot_user(self._user_id)
            list_for_show = get_personal_list(pk_bot_guest)
            
            # 2 выдаем кандидатов по одному...
            for candidat in list_for_show:
                
                if candidat[3] != False:
                    result = self._get_describe_of_candidat(candidat)
                    vk_bot.write_msg(self._user_id, f"{result} \n\n")
                    
                    keyboard = VkKeyboard(one_time=True)
                    keyboard.add_button('like', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_button('dislike', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_button("don't know", color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('stop', color=VkKeyboardColor.NEGATIVE)
                    
                    vk_bot.write_msg(self._user_id, f"Like or dislike? Stop?", keyboard)
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW:
                            if event.to_me:
                                request = event.text
                                if "dislike" in request.lower():
                                    print('не зашло, поставить в базу дизлайк')
                                    add_like_to_db(candidat[0], False)
                                    break
                                elif "like" in request.lower():
                                    print('поставить в базу лайк')
                                    add_like_to_db(candidat[0], True)
                                    break
                                elif "stop" in request.lower():
                                    return 'stop'
                                else:
                                    print('решит потом')
                                    break
                else:
                    print('пропускаем этого кантидата')
                                
            return ('список просмотрен, кандидатов больше нет. \n'
                    'lista pregledana, više nema kandidata.')
        
        # start
        # запускаем поиск и вносим в базу гостя, кандидатов, связку между ними
        elif 'start' in message.lower() or 'старт' in message.lower():
            
            user_descript = vk_bot.get_user_info()
            if 'bdate' not in list(user_descript):
                del_user(self._user_id)
                return (f'Привет (čao), {self._user_name}!'
                        f' У тебя не указана дата рождения, '
                        f'т.е. нет информации возрасте. Поиск в данном случае не работает. '
                        f'Можешь исправить настройки профиля и зайти сюда снова. \n'
                        f'Nemate datum rođenja, nema podataka o starosti. Pretraga'
                        f' u ovom slučaju ne radi, možete popraviti podešavanja profila '
                        f'i ponovo otići ovde')
            
            if '.' in user_descript['bdate'][-4:]:
                del_user(self._user_id)
                return (f'Привет (čao), {self._user_name}!'
                        f' У тебя указана дата рождения (Imate datum rođenja): '
                        f'{user_descript['bdate'][-4:]}, '
                        f'т.е. нет информации возрасте. Поиск в данном случае не работает. '
                        f'Можешь исправить настройки профиля и зайти сюда снова. \n'
                        f'nema podataka o starosti. Pretraga u ovom slučaju ne funkcioniše. '
                        f'Možete popraviti podešavanja profila i ponovo otići ovde.')
            
            vk_bot.write_msg(self._user_id, f"сколько кандидатов попробуем подобрать (от 1 до 1000)? \n"
                                            f"koliko kandidata ćemo pokušati da izaberemo (od 1 do 1000)? \n")
            
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        request = event.text
                        if request.isdigit():
                            if 0 < int(request) < 1001:
                                pk_bot_guest = get_bot_user(self._user_id)
                                count_in_db = len(get_personal_list(pk_bot_guest))
                                count_for_search = int(request) + count_in_db
                                break
                        return (f'{self._user_name}, \n для корректной работы бота необходимо'
                                f'следовать его инструкциям. В данном случае, необходимо было '
                                f'ввести целое число от 1 до 1000 включительно. (Da bi bot pravilno '
                                f'funkcionisao, morate slediti njegova uputstva. '
                                f'U ovom slučaju, bilo je potrebno uneti ceo broj od 1 do 1000.)')
            
            
            vk_bot.write_msg(self._user_id, f"Поиск займет несколько минут..."
                                            f"(Pretraga će trajati nekoliko minuta...)")
            # 1. вносим гостя в базу (если его еще там нет)
            
            if get_bot_user(self._user_id):
                print(f'bot_guest {self._user_id} есть в базе')
            else:
                add_user(self._user_id)
                print(f'bot_guest {self._user_id} добавлен в базу')
            
            # 2. запускаем поиск кандидатов
            candidads = vk_bot.get_candidats(user_descript['candidate_sex'],
                                             user_descript['city']['id'],
                                             user_descript['bdate'][-4:],
                                             self._user_id,
                                             count_for_search)
            if candidads == []:
                # поиск по городу не дал результатов, запускаем расширенный поиск
                self._users_search_extend = True
                candidads = vk_bot.get_candidats_extend(user_descript['candidate_sex'],
                                                        user_descript['country']['id'],
                                                        user_descript['bdate'][-4:],
                                                        self._user_id,
                                                        count_for_search)
            print(f'{candidads=}')
            if candidads == []:
                message_for_user = (f"Поиск не дает новых кандидатов. "
                                    f"Подождите немного или попробуйте изменить город своего профиля"
                                    f" для поиска в других регионах.\n(Pretraga ne daje više novih "
                                    f"kandidata. Sačekajte malo) \n\n")
            else:
                message_for_user = ''
                
            message_for_user += (f"{user_descript["first_name"]},\n"
                                f"что бы ознакомиться с имеющейся подборкой\n"
                                f"кандидатов набери команду \n(da biste se upoznali "
                                f"sa dostupnim izborom kandidata) :    next/show' ")
            return message_for_user
        
        # Пока
        elif 'пока' in message.lower() or 'stop' in message.lower():
            return f"Чао (čao), {self._user_name}!"
        
        else:
            return ("Не понимаю о чем вы. Список возможных команд вызывается 'help' \n"
                    "Ne razumem. Poziva 'Help'")
    
    def write_msg(self, user_id, message, keyboard=None):
        post = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if keyboard != None:
            post['keyboard'] = keyboard.get_keyboard()
        print(f'{post=}')
        vk.method('messages.send', post)
    
    def write_msg_foto(self, user_id, user_vk, id_photo, message):
        attachment = f'photo{user_vk}_{id_photo}'
        vk.method('messages.send',
                  {'peer_id': user_id, 'message': message, 'attachment': attachment, 'random_id': randrange(10 ** 7)})


if __name__ == '__main__':
    
    print('start')
    
    vk = vk_api.VkApi(token=bot_token)
    longpoll = VkLongPoll(vk)
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                vk_bot = VK_client_bot_guest(owner_token, owner_id, bot_token, bot_id, event.user_id)
                vk_bot.write_msg(event.user_id, vk_bot.new_message(event.text))
                print('Text: ', event.text)


