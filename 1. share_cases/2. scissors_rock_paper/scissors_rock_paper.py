import random
SRP=["Scissor","Rock","Paper"]

while True:
    computer_input=random.randint(0,2)
    computer_pos=SRP[computer_input]
    my_input=eval(input("Select:1 Scissor,2 Rock,3 Paper"))
    my_pos="Scissor"
    if my_input == 1 :
        my_pos = "Scissor"
    elif my_input == 2 :
        my_pos = "Rock"
    else:
        my_pos = "Paper"
    print("I do："+my_pos)
    print("Computer do："+computer_pos)
    combine = {
        "ScissorRock": "Computer Win!",
        "RockScissor": "I Win!",
        "RockPaper": "Computer Win!",
        "PaperRock": "I Win!",
        "PaperScissor": "Computer Win!",
        "ScissorPaper": "I Win!",
    }
    if my_pos+computer_pos in combine:
        print(combine[my_pos+computer_pos])
    else:
        print("Draw!")
