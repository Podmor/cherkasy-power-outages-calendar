# cherkasy-power-outages-calendar

Календарі планових відключень світла для Черкас і Черкаської області: окремий календар для кожної з 12 підчерг (від 1.1 до 6.2). Бот сам читає офіційний Telegram-канал Черкасиобленерго і оновлює файли календарів, на які можна підписатися на телефоні. Працює безкоштовно на GitHub Actions, комп'ютер вмикати не потрібно.

*English: calendar feeds of planned power outages in Cherkasy region, one per subqueue (1.1 to 6.2). A bot reads the official Telegram channel of the utility and publishes `.ics` calendars. Runs for free on GitHub Actions.*

## Підписка

Сторінка з кнопками для всіх підчерг: **https://podmor.github.io/cherkasy-power-outages-calendar/**

| Черга | iPhone / Mac | Google Календар | Файл |
|-------|--------------|-----------------|------|
| 1.1 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/1.1.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F1.1.ics) | [1.1.ics](https://podmor.github.io/cherkasy-power-outages-calendar/1.1.ics) |
| 1.2 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/1.2.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F1.2.ics) | [1.2.ics](https://podmor.github.io/cherkasy-power-outages-calendar/1.2.ics) |
| 2.1 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/2.1.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F2.1.ics) | [2.1.ics](https://podmor.github.io/cherkasy-power-outages-calendar/2.1.ics) |
| 2.2 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/2.2.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F2.2.ics) | [2.2.ics](https://podmor.github.io/cherkasy-power-outages-calendar/2.2.ics) |
| 3.1 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/3.1.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F3.1.ics) | [3.1.ics](https://podmor.github.io/cherkasy-power-outages-calendar/3.1.ics) |
| 3.2 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/3.2.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F3.2.ics) | [3.2.ics](https://podmor.github.io/cherkasy-power-outages-calendar/3.2.ics) |
| 4.1 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/4.1.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F4.1.ics) | [4.1.ics](https://podmor.github.io/cherkasy-power-outages-calendar/4.1.ics) |
| 4.2 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/4.2.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F4.2.ics) | [4.2.ics](https://podmor.github.io/cherkasy-power-outages-calendar/4.2.ics) |
| 5.1 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/5.1.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F5.1.ics) | [5.1.ics](https://podmor.github.io/cherkasy-power-outages-calendar/5.1.ics) |
| 5.2 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/5.2.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F5.2.ics) | [5.2.ics](https://podmor.github.io/cherkasy-power-outages-calendar/5.2.ics) |
| 6.1 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/6.1.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F6.1.ics) | [6.1.ics](https://podmor.github.io/cherkasy-power-outages-calendar/6.1.ics) |
| 6.2 | [Apple](webcal://podmor.github.io/cherkasy-power-outages-calendar/6.2.ics) | [Google](https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F6.2.ics) | [6.2.ics](https://podmor.github.io/cherkasy-power-outages-calendar/6.2.ics) |

Свою підчергу можна дізнатися за адресою на [сайті Черкасиобленерго](https://www.cherkasyoblenergo.com/off).

**iPhone:** Налаштування → Календар → Облікові записи → Додати обліковий запис → Інше → Додати підписаний календар → вставити посилання (або просто натиснути кнопку «Apple»).
**Mac:** Календар → Файл → Нова підписка на календар.

Календар лише для читання. Події оновлюються самі: якщо графік змінився, час події міняється, а скасоване відключення зникає. Перед кожним відключенням є нагадування за 15 хвилин. Телефон сам вирішує, як часто оновлювати підписку, тому зміни можуть з'являтися із запізненням до кількох годин.

## Як це працює

1. Раз на 15 хвилин запускається `python -m outage_calendar`.
2. Бот читає публічну сторінку офіційного каналу `t.me/s/pat_cherkasyoblenergo` (логін і ключі не потрібні).
3. Із повідомлень «Години відсутності електропостачання» для кожної дати і кожної підчерги береться список годин без світла.
4. Оновлення, що виходить протягом дня, містить лише години, які ще попереду (відключення, яке йде зараз, вказане повністю). Бот зберігає години, що вже минули, а решту дня замінює новим списком. Повідомлення, опубліковане до початку доби, замінює день повністю.
5. Сусідні години об'єднуються в одну подію, також через північ.
6. Якщо найновіше повідомлення прочитати не вдалося, запуск завершується помилкою, і GitHub надсилає лист власнику репозиторію.

Стан зберігається у `state/`, готові календарі та сторінка з посиланнями у `docs/` (їх віддає GitHub Pages).

## Налаштування

Усе в `config.json`: канал, список підчерг (`queues`), час нагадувань у хвилинах (`alarm_minutes`), адреса сайту (`site_url`). Нова підчерга з'являється, щойно її додано до `queues`.

## Розробка

```
pip install -r requirements-dev.txt
python -m pytest
python -m outage_calendar
```

Тести містять справжні повідомлення каналу за 6–8 жовтня 2026 року. Модуль `outage_calendar/wheel.py` розпізнає картинки-годинники з неофіційних каналів із графіками. Зараз він не використовується і лишається як запасний варіант.
