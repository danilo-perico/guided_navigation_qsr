import random

number_experiments = 100
robots = 4
target = 1

for j in range(robots):
    with open("robots.dat", "w") as f:
        pass
    
for i in range(0, number_experiments):
    with open("target.dat", "w") as f:
        pass


for i in range(0, number_experiments*robots):
    with open("robots.dat", "a") as f:
        f.write(str(random.randint(250, 750)) + " " + str(random.randint(250, 750)) + " " + str(random.randrange(0, 315, 45)) + "\n")

for i in range(0, number_experiments):
    with open("target.dat", "a") as f:
        f.write(str(random.randint(250, 750)) + " " + str(random.randint(250, 750)) + "\n") 
