# This is a complex test file

label start:
    e "Welcome, [player_name]!"

    # A very long line to test chunking
    e "This is a very long line of text designed to test the chunking functionality of the translation API wrapper. It repeats the same sentence over and over to easily exceed the character limit of most translation services, which is typically around 5000 characters per request. By splitting this text into smaller sentences, the tool should be able to translate the entire paragraph without encountering an API error. This sentence will be repeated many times. This is a very long line of text designed to test the chunking functionality of the translation API wrapper. It repeats the same sentence over and over to easily exceed the character limit of most translation services, which is typically around 5000 characters per request. By splitting this text into smaller sentences, the tool should be able to translate the entire paragraph without encountering an API error. This sentence will be repeated many times. This is a very long line of text designed to test the chunking functionality of the translation API wrapper. It repeats the same sentence over and over to easily exceed the character limit of most translation services, which is typically around 5000 characters per request. By splitting this text into smaller sentences, the tool should be able to translate the entire paragraph without encountering an API error. This sentence will be repeated many times. This is a very long line of text designed to test the chunking functionality of the translation API wrapper. It repeats the same sentence over and over to easily exceed the character limit of most translation services, which is typically around 5000 characters per request. By splitting this text into smaller sentences, the tool should be able to translate the entire paragraph without encountering an API error. This sentence will be repeated many times. This is a very long line of text designed to test the chunking functionality of the translation API wrapper. It repeats the same sentence over and over to easily exceed the character limit of most translation services, which is typically around 5000 characters per request. By splitting this text into smaller sentences, the tool should be able to translate the entire paragraph without encountering an API error. This sentence will be repeated many times. This is a very long line of text designed to test the chunking functionality of the translation API wrapper. It repeats the same sentence over and over to easily exceed the character limit of most translation services, which is typically around 5000 characters per request. By splitting this text into smaller sentences, the tool should be able to translate the entire paragraph without encountering an API error. This sentence will be repeated many times."

translate spanish:
    # This block should be translated
    old "This has a {b}bold tag{/b}."
    new "This has a {b}bold tag{/b}."

    # This is a comment between old and new
    old "This line has a comment after it."

    # Some comment

    new "This line has a comment after it."

    # This block should be skipped
    old "This is already done."
    new "Esto ya está hecho."
