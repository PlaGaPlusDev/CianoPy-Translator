label options_menu:
    menu:
        "First option":
            jump choice_one
        "Second option with a %(value)s format":
            jump choice_two
        "The last option":
            jump choice_three

label choice_one:
    e "You picked the first one."
    jump end_of_menu

label choice_two:
    e "You picked the second one."
    jump end_of_menu

label choice_three:
    e "You picked the third one."
    jump end_of_menu

label end_of_menu:
    "End of the menu."
    return
