import pandas as pd
import random
from datetime import datetime, timedelta

def generate_synthetic_phishing_email():
    # Define different types of phishing scenarios
    scenarios = {
        'bank': {
            'templates': [
                "Уважаемый клиент {bank_name}, Ваша карта {card_status}...",
                "Служба безопасности {bank_name}: обнаружена попытка входа из {location}..."
            ],
            'organizations': ["Сбербанк", "ВТБ", "Тинькофф", "Альфа-Банк"],
            'domains': ["security-bank.ru", "bank-online.ru", "secure-banking.ru"]
        },
        'online_shop': {
            'templates': [
                "Ваш заказ #{order_number} из {shop_name} готов к выдаче...",
                "Получите скидку {discount}% в {shop_name} прямо сейчас!"
            ],
            'organizations': ["Wildberries", "Ozon", "AliExpress", "Яндекс.Маркет"],
            'domains': ["market-delivery.ru", "online-shop.ru", "delivery-express.ru"]
        },
        'government': {
            'templates': [
                "Уведомление о штрафе: {fine_amount} руб. Оплатите в течение {days} дней...",
                "Портал Госуслуг: Вам начислена компенсация {amount} руб..."
            ],
            'organizations': ["Госуслуги", "ФНС России", "МВД России"],
            'domains': ["gov-services.ru", "tax-portal.ru", "mvd-notice.ru"]
        },
        'social_media': {
            'templates': [
                "Ваш аккаунт {platform} был временно заблокирован...",
                "Обнаружен подозрительный вход в ваш профиль {platform}..."
            ],
            'organizations': ["ВКонтакте", "Одноклассники", "Telegram"],
            'domains': ["vk-security.ru", "ok-account.ru", "telegram-verify.ru"]
        }
    }
    
    # Randomly select a scenario
    scenario_type = random.choice(list(scenarios.keys()))
    scenario = scenarios[scenario_type]
    
    # Generate dynamic values
    order_number = random.randint(100000, 999999)
    fine_amount = random.randint(1000, 10000)
    discount = random.randint(50, 90)
    amount = random.randint(3000, 15000)
    days = random.randint(3, 10)
    location = random.choice(["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург"])
    
    # Create the email
    selected_org = random.choice(scenario['organizations'])
    email = {
        'scenario_type': scenario_type,
        'sender': f"service_{random.randint(1000,9999)}@{random.choice(scenario['domains'])}",
        'subject': f"Важное уведомление от {selected_org}",
        'body': random.choice(scenario['templates']).format(
            bank_name=selected_org,
            card_status="временно заблокирована",
            shop_name=selected_org,
            order_number=order_number,
            platform=selected_org,
            fine_amount=fine_amount,
            discount=discount,
            amount=amount,
            days=days,
            location=location
        ),
        'organization': selected_org,
        'is_phishing': True,
        'timestamp': datetime.now() - timedelta(days=random.randint(1,30))
    }
    
    return email

# # Generate a diverse dataset
# emails = [generate_synthetic_phishing_email() for _ in range(1000)]
# df = pd.DataFrame(emails)

def generate_legitimate_email():
    # Templates for legitimate business communications
    templates = {
        'business': {
            'templates': [
                "Уважаемый {name}, направляю вам отчет за {month} месяц...",
                "Добрый день! Напоминаем о встрече {meeting_topic}, запланированной на {time}...",
                "Информируем вас о плановых технических работах {date}..."
            ],
            'domains': ["company.ru", "business.ru", "corp.ru"],
            'names': ["Александр", "Елена", "Дмитрий", "Ольга"],
            'topics': ["по проекту", "с клиентом", "команды разработчиков"]
        },
        'service': {
            'templates': [
                "Ваш заказ №{order_id} успешно оформлен. Детали доставки...",
                "Подтверждение бронирования #{booking_id}. Дата: {date}",
                "Спасибо за оплату услуг. Квитанция во вложении..."
            ],
            'domains': ["shop.ru", "service.ru", "support.ru"]
        }
    }
    
    category = random.choice(list(templates.keys()))
    scenario = templates[category]
    
    email = {
        'type': 'legitimate',
        'sender': f"{random.choice(scenario['domains'])}",
        'subject': "Информация по вашему запросу",
        'body': random.choice(scenario['templates']).format(
            name=random.choice(templates['business']['names']),
            month=random.choice(["январь", "февраль", "март"]),
            meeting_topic=random.choice(templates['business']['topics']),
            time="14:00",
            date="15.12.2024",
            order_id=random.randint(10000, 99999),
            booking_id=random.randint(1000, 9999)
        ),
        'is_phishing': False,
        'timestamp': datetime.now() - timedelta(days=random.randint(1,30))
    }
    
    return email

# Generate both types of emails with realistic proportions
# In real email traffic, phishing emails are much less common than legitimate ones
num_total = 1000
phishing_ratio = 0.2  # 20% phishing, 80% legitimate

num_phishing = int(num_total * phishing_ratio)
num_legitimate = num_total - num_phishing

# Generate both types
phishing_emails = [generate_synthetic_phishing_email() for _ in range(num_phishing)]
legitimate_emails = [generate_legitimate_email() for _ in range(num_legitimate)]

# Combine into one dataset
all_emails = phishing_emails + legitimate_emails
df = pd.DataFrame(all_emails)

# Shuffle the dataset to mix phishing and legitimate emails
df = df.sample(frac=1).reset_index(drop=True)

print(df.head(3))

# Save to CSV file
df.to_csv('russian_phishing_dataset.csv', index=False)

print(df['scenario_type'].value_counts())