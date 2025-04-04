import requests

def check_deeplink_status_api(deeplink_id):
    """
    Проверяет статус диплинка через API Tripster, делая один или два запроса:
    1.  Проверяет, существует ли экскурсия как активная.
    2.  Если экскурсия не найдена как активная, проверяет, существует ли она как неактивная.

    Args:
        deeplink_id (int): ID диплинка.

    Returns:
        tuple: (is_active, reason, title)
               is_active (bool): True, если экскурсия активна, False - если неактивна.
               reason (str): Причина неактивности (если известна), иначе None.
               title (str): Название экскурсии.
    """
    api_url = "https://experience.tripster.ru/api/partners/travelpayouts/search/experiences/"

    try:
        # 1. Проверяем, существует ли экскурсия как активная (без параметра paused)
        params_exists = {
            "ids": deeplink_id,
        }
        url_exists = f"{api_url}?ids={deeplink_id}"

        response_exists = requests.get(api_url, params=params_exists)
        response_exists.raise_for_status()
        data_exists = response_exists.json()

        if data_exists["count"] > 0 and data_exists["results"]:
            # Экскурсия существует!
            experience = data_exists["results"][0]
            title = experience["title"]  # Получаем название
            is_active = experience["status"] == "active" #  Определяем, активна ли экскурсия

            if is_active:
                # Экскурсия активна, нет смысла проверять дальше
                reason = None
                return is_active, reason, title
            else:
                #Экскурсия существует, но не активна, reason тоже пока нет
                reason = None
                
        else:
            # Экскурсия не найдена как активная
            title = "Экскурсия не найдена"
            is_active = False
            reason = "Экскурсия не найдена в API"


        # Если дошли до этого места, значит, экскурсия либо не найдена, либо она неактивна
        # Проверяем, существует ли экскурсия как неактивная (с параметром paused=true)
        params_paused = {
            "ids": deeplink_id,
            "paused": True
        }

        url_paused = f"{api_url}?ids={deeplink_id}&paused=true"

        response_paused = requests.get(api_url, params=params_paused)
        response_paused.raise_for_status()
        data_paused = response_paused.json()

        if data_paused["count"] > 0 and data_paused["results"]:
            # Экскурсия найдена как неактивная, значит берем title отсюда
             experience = data_paused["results"][0]
             title = experience["title"]
        
        return is_active, reason, title #Возвращаем результат

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return False, f"Ошибка API: {e}", None
    except Exception as e:
        print(f"Ошибка при обработке ответа API: {e}")
        return False, f"Ошибка обработки API: {e}", None