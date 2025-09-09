# A test script for the translator

label start:
    e "Hello, world!"
    e "This is a test of the translation tool."

    "This line has no character tag."

    e "This line has a {b}bold tag{/b} and an {i}italic tag{/i}."
    e "This line has a variable for the player's name: [player_name]."

    # This block is already translated and should be skipped if the option is on.
    translate spanish:
        old "This is a pre-translated line."
        new "Esta es una línea pre-traducida."

    e "This is the final line."

    return
