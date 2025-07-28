from datu.anonymization.base_anonymizer import PiiAnonymizer


def test_phone_number_anonymization():
    """Test anonymization and deanonymization of phone numbers."""
    anonymizer = PiiAnonymizer()
    text = "My phone number is 123-456-7890."
    anonymized_text = anonymizer.anonymize(text)
    assert anonymized_text != text
    assert "PHONE_NUMBER" in anonymized_text
    assert anonymizer.deanonymize(anonymized_text) == text


def test_email_address_anonymization():
    """Test anonymization and deanonymization of email addresses."""
    anonymizer = PiiAnonymizer()
    text = "My email is example@gmail.com"
    anonymized_text = anonymizer.anonymize(text)
    assert anonymized_text != text
    assert "EMAIL_ADDRESS" in anonymized_text
    assert anonymizer.deanonymize(anonymized_text) == text


def test_credit_card_anonymization():
    """Test anonymization and deanonymization of credit card numbers."""
    anonymizer = PiiAnonymizer()
    text = "My credit card number is 4111-1111-1111-1111."
    anonymized_text = anonymizer.anonymize(text)
    assert anonymized_text != text
    assert "CREDIT_CARD" in anonymized_text
    assert anonymizer.deanonymize(anonymized_text) == text
