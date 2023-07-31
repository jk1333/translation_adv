from google.cloud import translate_v3 as translate
import sys

#최대 용어집은 1만개 까지 가능하며 hard limit입니다.
project_id = sys.argv[1]
glossary_id = "test_chat_translation"
#CSV file 은 하기 pandas dataframe에서 생성하니 bucket path 만 본인것으로 바꿔 주시면 됩니다.
input_uri=f"gs://{sys.argv[2]}/synonym.csv"
location = "global"

#용어모음집을 사용하여 번역한다.
def translate_text_with_glossary(text, source, target, client, glossary_config):
    """Translates a given text using a glossary."""

    #client = translate.TranslationServiceClient.from_service_account_json("/path/to/file")
    parent = f"projects/{project_id}/locations/{location}"

    # Supported language codes: https://cloud.google.com/translate/docs/languages
    response = client.translate_text(
        request={
            "contents": [text],
            "target_language_code": target,
            "source_language_code": source,
            "parent": parent,
            "glossary_config": glossary_config
        }
    )

    print("Translated text: \n")
    for translation in response.glossary_translations:
        print("\t {}".format(translation.translated_text))

#용어집을 GCP 리소스로 생성한다
def create_glossary(glossary_df, timeout=180):
    glossary_df.to_csv(input_uri)
    """
    Create a equivalent term sets glossary. Glossary can be words or
    short phrases (usually fewer than five words).
    https://cloud.google.com/translate/docs/advanced/glossary#format-glossary
    """
    client = translate.TranslationServiceClient()

    # Supported language codes: https://cloud.google.com/translate/docs/languages

    name = client.glossary_path(project_id, location, glossary_id)
    language_codes_set = translate.types.Glossary.LanguageCodesSet(
        language_codes=glossary_df.columns.values
    )

    gcs_source = translate.types.GcsSource(input_uri=input_uri)

    input_config = translate.types.GlossaryInputConfig(gcs_source=gcs_source)

    glossary = translate.types.Glossary(
        name=name, language_codes_set=language_codes_set, input_config=input_config
    )

    parent = f"projects/{project_id}/locations/{location}"
    # glossary is a custom dictionary Translation API uses
    # to translate the domain-specific terminology.
    operation = client.create_glossary(parent=parent, glossary=glossary)

    result = operation.result(timeout)
    print("Created: {}".format(result.name))
    print("Input Uri: {}".format(result.input_config.gcs_source.input_uri))

#용어집을 GCP 리소스에서 삭제한다
def delete_glossary(timeout=180):
    """Delete a specific glossary based on the glossary ID."""
    client = translate.TranslationServiceClient()

    name = client.glossary_path(project_id, "us-central1", glossary_id)

    operation = client.delete_glossary(name=name)
    result = operation.result(timeout)
    print("Deleted: {}".format(result.name))


client = translate.TranslationServiceClient()
glossary = client.glossary_path(project_id, location, glossary_id)
glossary_config = translate.TranslateTextGlossaryConfig(glossary=glossary, ignore_case = True)

import pandas as pd

#모든 용어집은 대소문자를 구분함
#동의어 세트 (여러 언어의 용어를 지정),
#만약 번역을 원하지 않는다면 같은 워드를 지정, 아래 예시에서 en: JK는 일본어에서는 번역하지 않고, 한국어에서는 번역하게 함
#국가별 언어코드 참고(ISO-639): https://cloud.google.com/translate/docs/languages
synonym_df = pd.DataFrame(columns=['en', 'ko', 'ja'])
synonym_df = pd.concat([synonym_df, pd.DataFrame([{'en': "JK", 'ko': "지혁", 'ja': "JK"}])], axis=0, ignore_index=True)

print("용어집 정보")
print(synonym_df)

#용어집을 생성한다.
#create_glossary(synonym_df)

#용어집을 삭제한다.
#delete_glossary()

translate_text_with_glossary("<from id='Hello'>Hello jk!, Hello <to id='@𝖿𝖺𝗇'></to></from>", "en", "ko", client, glossary_config)

translate_text_with_glossary("<from id='Hello'>Hello JK!, Hello <to id='@𝖿𝖺𝗇'>text</to></from>", "en", "ja", client, glossary_config)

translate_text_with_glossary("Hello JK!, Hello <span translate='no'>@𝖿𝖺𝗇</span>", "en", "ko", client, glossary_config)

