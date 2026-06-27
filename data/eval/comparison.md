# E2 — Generic LLM vs. Journey-Guided (Integreat Compass)

Ran 10 questions from `test_questions.csv` through both a plain LLM and our pipeline. The system is **options-first** (it clarifies before answering) and **source-grounded** (every answer cites live Integreat pages).

## Q01 — I just came to Germany. What do I do first?
- **lang/expected journey:** en / `arrival_first_steps`
- **Generic LLM (no grounding):** Willkommen in Deutschland! Zuerst solltest du dich um folgende Dinge kümmern:  1. **Anmeldung**: Melde dich innerhalb von zwei Wochen nach deiner Ankunft bei der zuständigen Behörde (Bürgeramt) an. 2. **Bankkonto**: Eröffne ein deutsches Bankkonto, um Geld zu verwalten und Zahlungen zu tätigen. 3. **Versicherung**: Informiere dich über Krankenversicherungen und schließe eine ab. 4. **Sprache**: Üb
- **Journey-guided →** journey `address_registration`, clarifying questions asked: 2, handoff: False
  - **grounded answer:** To register your address in Munich, you need to visit the citizens' office in person or register online if you have an online ID. An appointment is required.
  - **sources cited:** Wohnsitz anmelden / ummelden (2024-12-03T12:48:27.092+01:00); Register / re-register residence (2024-12-03T12:48:33.719+01:00); Neu in München? Hier finden Sie Erste Schritte (2026-02-02T11:59:03.576+01:00); Wohnungssuche (2025-06-20T15:01:57.688+02:00); New in Munich? Here you can find first steps (2026-01-07T13:38:58.056+01:00)

## Q02 — I found an apartment and need to register my address
- **lang/expected journey:** en / `address_registration`
- **Generic LLM (no grounding):** To register your address, you typically need to follow these steps:  1. **Gather Required Documents**: This may include your lease agreement, identification, and any other documents required by your local authority.     2. **Visit Local Authority Office**: Go to your local government or municipal office responsible for address registration.  3. **Complete Registration Form**: Fill out any necessar
- **Journey-guided →** journey `address_registration`, clarifying questions asked: 1, handoff: False
  - **grounded answer:** To register your address in Munich, you need to visit the citizens' office in person and make an appointment. Bring the required documents.
  - **sources cited:** Wohnsitz anmelden / ummelden (2024-12-03T12:48:27.092+01:00); Register / re-register residence (2024-12-03T12:48:33.719+01:00); Neu in München? Hier finden Sie Erste Schritte (2026-02-02T11:59:03.576+01:00); Wohnungssuche (2025-06-20T15:01:57.688+02:00); New in Munich? Here you can find first steps (2026-01-07T13:38:58.056+01:00)

## Q03 — أين يمكنني تسجيل عنوان سكني الجديد؟
- **lang/expected journey:** ar / `address_registration`
- **Generic LLM (no grounding):** يمكنك تسجيل عنوان سكني جديد في الجهة المختصة في بلدك، مثل وزارة الداخلية أو الهيئة المسؤولة عن السجل المدني. يُفضل زيارة الموقع الرسمي للجهة المعنية أو الاتصال بهم للحصول على التفاصيل الدقيقة والإجراءات المطلوبة.
- **Journey-guided →** journey `address_registration`, clarifying questions asked: 1, handoff: False
  - **grounded answer:** لتسجيل عنوان سكنك في ميونيخ، يجب عليك زيارة مكتب المواطنين شخصيًا. يجب أن يكون لديك موعد مسبق.
  - **sources cited:** Wohnsitz anmelden / ummelden (2024-12-03T12:48:27.092+01:00); Register / re-register residence (2024-12-03T12:48:33.719+01:00); Neu in München? Hier finden Sie Erste Schritte (2026-02-02T11:59:03.576+01:00); Wohnungssuche (2025-06-20T15:01:57.688+02:00); New in Munich? Here you can find first steps (2026-01-07T13:38:58.056+01:00)

## Q04 — أنا في ميونخ. أحتاج تسجيل الأطفال في الروضة ودورة لغة ألمانية
- **lang/expected journey:** ar / `school_childcare,german_course`
- **Generic LLM (no grounding):** يمكنك تسجيل الأطفال في الروضة من خلال زيارة موقع المدينة الرسمي أو الاتصال بالروضة القريبة منك. بالنسبة لدورة اللغة الألمانية، يمكنك البحث عن مراكز تعليمية أو معاهد لغة في ميونخ، مثل "Goethe-Institut" أو "Volkshochschule". تأكد من التحقق من المواعيد والتسجيل المسبق.
- **Journey-guided →** journey `school_childcare`, clarifying questions asked: 2, handoff: False
  - **grounded answer:** للتسجيل في حضانة (Kita) في ميونيخ، يجب عليك استخدام بوابة kita finder+، حيث يمكنك التسجيل لطفلك في عدة مؤسسات.
  - **sources cited:** Information about Kitas and how to register (2023-12-22T13:39:31.784+01:00); Anmeldung und Information zur Kita (2023-12-22T13:39:31.680+01:00); General information about the daycare centre (2026-02-12T13:34:32.437+01:00); Children's day centres (KiTZ) (2024-09-04T12:57:19.494+02:00); Allgemeine Informationen zur Kita (2026-04-08T12:17:45.545+02:00)

## Q05 — I need a German language course. Am I eligible?
- **lang/expected journey:** en / `german_course`
- **Generic LLM (no grounding):** Um Ihnen zu helfen, benötige ich mehr Informationen über Ihre Situation. In der Regel sind viele Sprachkurse für alle offen, aber es kann spezifische Anforderungen oder Voraussetzungen geben. Wo möchten Sie den Kurs machen?
- **Journey-guided →** journey `german_course`, clarifying questions asked: 1, handoff: False
  - **grounded answer:** Integration courses in Germany teach German up to level B1 and include cultural insights. They are free for refugees and social benefit recipients. Eligibility includes EU citizens, late repatriates, and those with specific residence permits.
  - **sources cited:** Integrationskurse (2025-08-08T13:55:02.786+02:00); Integration courses (2026-03-16T15:53:23.970+01:00); Deutschkurse der Stadt München (2025-03-12T13:17:14.594+01:00); Інтеграційні курси (2025-09-05T01:25:34.710+02:00); Search for German / integration courses yourself: Information platform BAMF-NAvI (2025-01-20T11:29:32.383+01:00)

## Q06 — How do I get health insurance?
- **lang/expected journey:** en / `health_insurance`
- **Generic LLM (no grounding):** To get health insurance, you can follow these steps:  1. **Determine Your Needs**: Assess your healthcare needs and budget. 2. **Research Options**: Look into different types of health insurance plans (employer-sponsored, government programs like Medicaid or Medicare, or private plans). 3. **Visit Healthcare.gov**: If you're in the U.S., you can explore options on the Health Insurance Marketplace 
- **Journey-guided →** journey `health_insurance`, clarifying questions asked: 1, handoff: False
  - **grounded answer:** In Germany, as an employed person, you are generally required to have health insurance. You can choose between statutory health insurance (Gesetzliche Krankenversicherung) and private health insurance (Private Krankenversicherung). Statutory health insurance covers a wide range of medical services, and you usually present your health insurance card when visiting a doctor. If you are low-income, yo
  - **sources cited:** Malteser relief service (2024-09-04T12:10:26.715+02:00); Clearingstelle Gesundheit (2024-05-29T14:09:05.727+02:00); Visit to the doctor (2025-09-05T01:03:10.615+02:00); New in Munich? Here you can find first steps (2026-01-07T13:38:58.056+01:00); Malteser Hilfsdienst (2024-09-04T12:10:20.354+02:00)

## Q07 — I have no place to stay tonight and no money. Help.
- **lang/expected journey:** en / `urgent_crisis,housing_search`
- **Generic LLM (no grounding):** I'm sorry to hear that you're in this situation. I recommend reaching out to local shelters or community organizations that can provide emergency housing. You can also contact friends or family for support. If you're in immediate danger, please call emergency services.
- **Journey-guided →** journey `urgent_crisis`, clarifying questions asked: 1, handoff: True
  - **grounded answer:** (reached handoff / clarification)
  - **sources cited:** —

## Q08 — Я з України. Мені потрібно записати дитину до школи
- **lang/expected journey:** uk / `school_childcare`
- **Generic LLM (no grounding):** Щоб записати дитину до школи в Україні, вам потрібно:  1. Визначити школу, до якої хочете записати дитину. 2. Зібрати необхідні документи: свідоцтво про народження дитини, паспорт одного з батьків, медичну довідку (форма 086-1/о). 3. Звернутися до школи, заповнити заяву на зарахування та подати документи.  Рекомендується також дізнатися про терміни прийому документів у конкретній школі.
- **Journey-guided →** journey `school_childcare`, clarifying questions asked: 2, handoff: False
  - **grounded answer:** Щоб знайти та зареєструватися на місце в дитячому садку (Kita) у Мюнхені, скористайтеся онлайн-порталом kita finder+. Рекомендується зареєструватися в кількох закладах, щоб підвищити шанси на отримання місця.
  - **sources cited:** Anmeldung und Information zur Kita (2023-12-22T13:39:31.680+01:00); Information about Kitas and how to register (2023-12-22T13:39:31.784+01:00); General information about the daycare centre (2026-02-12T13:34:32.437+01:00); Allgemeine Informationen zur Kita (2026-04-08T12:17:45.545+02:00); Children's day centres (KiTZ) (2024-09-04T12:57:19.494+02:00)

## Q09 — I do not have a landlord confirmation for the Anmeldung. What now?
- **lang/expected journey:** en / `address_registration`
- **Generic LLM (no grounding):** Ohne eine Bestätigung des Vermieters für die Anmeldung (Anmeldebestätigung) kannst du dich in Deutschland nicht offiziell anmelden. Du hast folgende Optionen:  1. **Vermieter kontaktieren**: Versuche, deinen Vermieter zu erreichen und bitte um die Bestätigung. 2. **Mietvertrag nutzen**: Manchmal akzeptieren die Behörden auch eine Kopie des Mietvertrags als Nachweis. 3. **Alternative Nachweise**: F
- **Journey-guided →** journey `address_registration`, clarifying questions asked: 2, handoff: False
  - **grounded answer:** To register your residence in Munich, you need to visit the citizens' office in person or register online if you have an online ID card. Make sure to book an appointment.
  - **sources cited:** Wohnsitz anmelden / ummelden (2024-12-03T12:48:27.092+01:00); Register / re-register residence (2024-12-03T12:48:33.719+01:00); Neu in München? Hier finden Sie Erste Schritte (2026-02-02T11:59:03.576+01:00); Wohnungssuche (2025-06-20T15:01:57.688+02:00); New in Munich? Here you can find first steps (2026-01-07T13:38:58.056+01:00)

## Q10 — Can you help me find a job and also do an Ausbildung?
- **lang/expected journey:** en / `work_ausbildung,german_course`
- **Generic LLM (no grounding):** Ja, ich kann dir Tipps geben, wie du einen Job und eine Ausbildung finden kannst. Du solltest deine Bewerbungsunterlagen vorbereiten, dich auf Jobportalen umsehen und dich bei Unternehmen in deiner Nähe bewerben. Außerdem kannst du dich bei der Agentur für Arbeit oder Berufsschulen informieren, die Ausbildungsplätze anbieten. Networking und Kontakte in deiner Branche können ebenfalls hilfreich sei
- **Journey-guided →** journey `work_ausbildung`, clarifying questions asked: 1, handoff: False
  - **grounded answer:** To find a job in Germany, you can seek support from the Munich Employment Agency, which offers free assistance for integration into work and training. Additionally, if you have foreign qualifications, you can explore recognition processes through various advisory services.
  - **sources cited:** Agentur für Arbeit München (2024-08-19T09:22:59.510+02:00); Munich Employment Agency (2024-08-19T09:23:10.485+02:00); Wie funktioniert die Anerkennung? (2025-09-15T15:09:50.299+02:00); Beratung für die Bereiche Industrie, Handel, Gastronomie und Dienstleistungen (2024-11-12T11:25:21.422+01:00); Servicestelle zur Erschließung ausländischer Qualifikationen (2024-07-12T13:21:45.115+02:00)
