export const LANGS = ["en", "de", "ar", "fa", "uk", "ru", "tr", "fr"] as const;
export type LangCode = (typeof LANGS)[number];

export const RTL_LANGS = new Set<string>(["ar", "fa"]);

export const LANG_NAMES: Record<LangCode, string> = {
  en: "English",
  de: "Deutsch",
  ar: "العربية",
  fa: "فارسی",
  uk: "Українська",
  ru: "Русский",
  tr: "Türkçe",
  fr: "Français",
};

export interface Strings {
  welcome_heading: string;
  welcome_subtitle: string;
  privacy_tagline: string;
  qs_register_label: string;
  qs_register_prompt: string;
  qs_housing_label: string;
  qs_housing_prompt: string;
  qs_german_label: string;
  qs_german_prompt: string;
  qs_health_label: string;
  qs_health_prompt: string;
  input_placeholder: string;
  input_placeholder_options: string;
  input_label: string;
  start_over: string;
  or_type_it: string;
  skip: string;
  retry_hint: string;
}

const translations: Record<LangCode, Strings> = {
  en: {
    welcome_heading: "How can I help you?",
    welcome_subtitle: "Your guide to life in Germany — housing, registration, health, courses.\nYour data stays on this device.",
    privacy_tagline: "Trusted guidance · your data stays on this device",
    qs_register_label: "Register my address",
    qs_register_prompt: "How do I register my address in Germany?",
    qs_housing_label: "Find housing",
    qs_housing_prompt: "How can I find an apartment as a newcomer in Germany?",
    qs_german_label: "Learn German",
    qs_german_prompt: "Where can I take a free German language course?",
    qs_health_label: "Get health insurance",
    qs_health_prompt: "How do I get health insurance in Germany?",
    input_placeholder: "Ask in your own words…",
    input_placeholder_options: "Or answer directly…",
    input_label: "Or type your question",
    start_over: "Start over",
    or_type_it: "Or type it",
    skip: "Skip",
    retry_hint: "Tap to retry the last step.",
  },
  de: {
    welcome_heading: "Wie kann ich helfen?",
    welcome_subtitle: "Ihr Wegweiser in Deutschland — Wohnen, Anmeldung, Gesundheit, Kurse.\nIhre Daten bleiben auf diesem Gerät.",
    privacy_tagline: "Vertrauensvolle Hilfe · Ihre Daten bleiben auf diesem Gerät",
    qs_register_label: "Adresse anmelden",
    qs_register_prompt: "Wie melde ich meine Adresse in Deutschland an?",
    qs_housing_label: "Wohnung finden",
    qs_housing_prompt: "Wie finde ich als Neuankömmling eine Wohnung in Deutschland?",
    qs_german_label: "Deutsch lernen",
    qs_german_prompt: "Wo kann ich einen kostenlosen Deutschkurs machen?",
    qs_health_label: "Krankenversicherung",
    qs_health_prompt: "Wie bekomme ich eine Krankenversicherung in Deutschland?",
    input_placeholder: "Stellen Sie Ihre Frage…",
    input_placeholder_options: "Oder direkt antworten…",
    input_label: "Oder schreiben Sie Ihre Frage",
    start_over: "Neu starten",
    or_type_it: "Oder tippen",
    skip: "Überspringen",
    retry_hint: "Tippen Sie, um den letzten Schritt zu wiederholen.",
  },
  ar: {
    welcome_heading: "كيف يمكنني مساعدتك؟",
    welcome_subtitle: "دليلك للحياة في ألمانيا — السكن، التسجيل، الصحة، الدورات.\nبياناتك تبقى على هذا الجهاز.",
    privacy_tagline: "إرشادات موثوقة · بياناتك تبقى على هذا الجهاز",
    qs_register_label: "تسجيل العنوان",
    qs_register_prompt: "كيف أسجّل عنواني في ألمانيا؟",
    qs_housing_label: "إيجاد سكن",
    qs_housing_prompt: "كيف أجد شقة كوافد جديد في ألمانيا؟",
    qs_german_label: "تعلم اللغة الألمانية",
    qs_german_prompt: "أين يمكنني أخذ دورة لغة ألمانية مجانية؟",
    qs_health_label: "التأمين الصحي",
    qs_health_prompt: "كيف أحصل على تأمين صحي في ألمانيا؟",
    input_placeholder: "اسأل بكلماتك الخاصة…",
    input_placeholder_options: "أو أجب مباشرة…",
    input_label: "أو اكتب سؤالك",
    start_over: "البدء من جديد",
    or_type_it: "أو اكتب",
    skip: "تخطي",
    retry_hint: "اضغط لإعادة المحاولة.",
  },
  fa: {
    welcome_heading: "چطور می‌توانم کمک کنم؟",
    welcome_subtitle: "راهنمای زندگی در آلمان — مسکن، ثبت‌نام، بهداشت، دوره‌ها.\nاطلاعات شما روی این دستگاه می‌ماند.",
    privacy_tagline: "راهنمایی مطمئن · اطلاعات شما روی این دستگاه می‌ماند",
    qs_register_label: "ثبت آدرس",
    qs_register_prompt: "چطور آدرسم را در آلمان ثبت کنم؟",
    qs_housing_label: "پیدا کردن مسکن",
    qs_housing_prompt: "چطور به عنوان تازه‌وارد در آلمان آپارتمان پیدا کنم؟",
    qs_german_label: "یادگیری زبان آلمانی",
    qs_german_prompt: "کجا می‌توانم دوره زبان آلمانی رایگان بگیرم؟",
    qs_health_label: "بیمه درمانی",
    qs_health_prompt: "چطور در آلمان بیمه درمانی بگیرم؟",
    input_placeholder: "سوال خود را بپرسید…",
    input_placeholder_options: "یا مستقیم پاسخ دهید…",
    input_label: "یا سوال خود را بنویسید",
    start_over: "شروع مجدد",
    or_type_it: "یا تایپ کنید",
    skip: "رد کردن",
    retry_hint: "برای تلاش مجدد ضربه بزنید.",
  },
  uk: {
    welcome_heading: "Як я можу допомогти?",
    welcome_subtitle: "Ваш путівник у Німеччині — житло, реєстрація, здоров'я, курси.\nВаші дані залишаються на цьому пристрої.",
    privacy_tagline: "Надійна допомога · ваші дані залишаються на цьому пристрої",
    qs_register_label: "Зареєструвати адресу",
    qs_register_prompt: "Як зареєструвати адресу в Німеччині?",
    qs_housing_label: "Знайти житло",
    qs_housing_prompt: "Як знайти квартиру як новоприбулий у Німеччині?",
    qs_german_label: "Вивчити німецьку",
    qs_german_prompt: "Де пройти безкоштовний курс німецької мови?",
    qs_health_label: "Медичне страхування",
    qs_health_prompt: "Як отримати медичне страхування в Німеччині?",
    input_placeholder: "Запитайте своїми словами…",
    input_placeholder_options: "Або відповідайте прямо…",
    input_label: "Або напишіть своє запитання",
    start_over: "Почати знову",
    or_type_it: "Або введіть",
    skip: "Пропустити",
    retry_hint: "Торкніться, щоб повторити останній крок.",
  },
  ru: {
    welcome_heading: "Чем я могу помочь?",
    welcome_subtitle: "Ваш путеводитель по Германии — жильё, регистрация, здоровье, курсы.\nВаши данные остаются на этом устройстве.",
    privacy_tagline: "Надёжная помощь · ваши данные остаются на этом устройстве",
    qs_register_label: "Зарегистрировать адрес",
    qs_register_prompt: "Как зарегистрировать адрес в Германии?",
    qs_housing_label: "Найти жильё",
    qs_housing_prompt: "Как найти квартиру новоприбывшему в Германии?",
    qs_german_label: "Учить немецкий",
    qs_german_prompt: "Где пройти бесплатный курс немецкого языка?",
    qs_health_label: "Медицинская страховка",
    qs_health_prompt: "Как получить медицинскую страховку в Германии?",
    input_placeholder: "Задайте вопрос своими словами…",
    input_placeholder_options: "Или ответьте напрямую…",
    input_label: "Или напишите свой вопрос",
    start_over: "Начать заново",
    or_type_it: "Или напечатайте",
    skip: "Пропустить",
    retry_hint: "Нажмите, чтобы повторить последний шаг.",
  },
  tr: {
    welcome_heading: "Size nasıl yardımcı olabilirim?",
    welcome_subtitle: "Almanya'da yaşam rehberiniz — konut, kayıt, sağlık, kurslar.\nVerileriniz bu cihazda kalır.",
    privacy_tagline: "Güvenilir rehberlik · verileriniz bu cihazda kalır",
    qs_register_label: "Adres kaydı yaptır",
    qs_register_prompt: "Almanya'da adresimi nasıl kaydettiririm?",
    qs_housing_label: "Konut bul",
    qs_housing_prompt: "Almanya'ya yeni gelen biri olarak nasıl daire bulabilirim?",
    qs_german_label: "Almanca öğren",
    qs_german_prompt: "Ücretsiz Almanca kursu nerede alabilirim?",
    qs_health_label: "Sağlık sigortası al",
    qs_health_prompt: "Almanya'da sağlık sigortası nasıl alınır?",
    input_placeholder: "Kendi kelimelerinizle sorun…",
    input_placeholder_options: "Ya da doğrudan yanıtlayın…",
    input_label: "Ya da sorunuzu yazın",
    start_over: "Yeniden başla",
    or_type_it: "Ya da yazın",
    skip: "Atla",
    retry_hint: "Son adımı tekrar denemek için dokunun.",
  },
  fr: {
    welcome_heading: "Comment puis-je vous aider ?",
    welcome_subtitle: "Votre guide pour la vie en Allemagne — logement, inscription, santé, cours.\nVos données restent sur cet appareil.",
    privacy_tagline: "Conseils fiables · vos données restent sur cet appareil",
    qs_register_label: "Enregistrer mon adresse",
    qs_register_prompt: "Comment enregistrer mon adresse en Allemagne ?",
    qs_housing_label: "Trouver un logement",
    qs_housing_prompt: "Comment trouver un appartement en tant que nouvel arrivant en Allemagne ?",
    qs_german_label: "Apprendre l'allemand",
    qs_german_prompt: "Où puis-je suivre un cours d'allemand gratuit ?",
    qs_health_label: "Assurance maladie",
    qs_health_prompt: "Comment obtenir une assurance maladie en Allemagne ?",
    input_placeholder: "Posez votre question…",
    input_placeholder_options: "Ou répondez directement…",
    input_label: "Ou écrivez votre question",
    start_over: "Recommencer",
    or_type_it: "Ou tapez",
    skip: "Ignorer",
    retry_hint: "Appuyez pour réessayer la dernière étape.",
  },
};

export function t(lang: string, key: keyof Strings): string {
  const code = (LANGS as readonly string[]).includes(lang) ? (lang as LangCode) : "en";
  return translations[code][key];
}

export function getStrings(lang: string): Strings {
  const code = (LANGS as readonly string[]).includes(lang) ? (lang as LangCode) : "en";
  return translations[code];
}

export function isRTL(lang: string): boolean {
  return RTL_LANGS.has(lang);
}
