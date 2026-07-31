/** Question ids of the seeded Health and Safety Incident Report template.
 *
 *  These are the fixed UUIDs in backend/app/sample_data/surveys.json. Naming them once
 *  keeps eight dictionaries from each repeating nine raw UUIDs, where a single mistyped
 *  character would silently leave one question in English on one locale.
 *
 *  If the template is ever republished with different questions, these stop matching and
 *  the form shows the API's own English wording — visibly wrong rather than quietly so.
 */
export const Q_WHEN = "a7e47b6c-2d28-52ec-8d9f-18445ff5fae2";
export const Q_AREA = "ef4fecac-f416-5cbb-95bb-59aa2e406d72";
export const Q_KIND = "47282484-404c-5822-9b80-b34ea4fc71e4";
export const Q_SEVERITY = "a88b448a-6593-5b0b-9b6d-f0dd5d79d065";
export const Q_WHAT = "cd6e03b9-68c5-5023-af49-6a2f6eab566e";
export const Q_PPE = "c75bc07f-fdb0-50d7-8563-27c5d355d7a4";
export const Q_HURT = "31a5f692-fe26-5fa5-a949-b96c09943e95";
export const Q_IMMEDIATE = "1ae5aedf-6165-55f3-b61e-3ce2ff03e137";
export const Q_PREVENT = "9ea79969-16fe-5be5-bd7a-cb73c0c43614";
