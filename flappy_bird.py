import pygame
import os
import random
import neat
import visualize
pygame.font.init()

WIN_WIDTH = 800
WIN_HEIGHT = 800

GEN = 0

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs","base.png")),(WIN_WIDTH,100))
BG_IMG = pygame.transform.scale(pygame.image.load("/Users/p0b00zy/flappy_bird_ai/imgs/bg.png"),(WIN_WIDTH,WIN_HEIGHT))
REWARD_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs","reward.png")),(50,50))

STAT_FONT = pygame.font.SysFont("comicsans",50)



class Reward:

    VEL = 5

    def __init__(self,x,y):
        self.img = REWARD_IMG
        self.x = x
        self.y = y

    def move(self):
        self.x -= self.VEL

    def draw(self,win):
        win.blit(self.img,(self.x,self.y))

    def collide(self,bird):
        bird_mask = bird.get_mask()
        reward_mask = pygame.mask.from_surface(self.img)

        offset = (self.x - bird.x, self.y-round(bird.y))

        collide = bird_mask.overlap(reward_mask,offset)

        if collide:
            return True
        return False


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION =  25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]
        self.is_alive = 1

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        displacement = self.vel*self.tick_count + 1.5*self.tick_count**2

        if displacement > 14:
            displacement = 14

        if displacement < 0:
            displacement-=2

        self.y += displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self,win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[0]
        else:
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img,self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x,self.y)).center)
        win.blit(rotated_image,new_rect.topleft)
    # list of pixels,used to find collision
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self,x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG,False,True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.WIDTH = PIPE_IMG.get_width()

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self,win):
        win.blit(self.PIPE_TOP,(self.x,self.top))
        win.blit(self.PIPE_BOTTOM,(self.x,self.bottom))

    def collide(self,bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top-round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom-round(bird.y))

        b_point = bird_mask.overlap(bottom_mask,bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)

        if t_point or b_point:
            return True
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1+self.WIDTH < 0:
            self.x1 = self.x2+self.WIDTH

        if self.x2+self.WIDTH < 0:
            self.x2 = self.x1+self.WIDTH

    def draw(self,win):
        win.blit(self.IMG,(self.x1,self.y))
        win.blit(self.IMG,(self.x2,self.y))

def draw_window(win,birds,pipes,base,score,gen,alive,reward):
    win.blit(BG_IMG,(0,0))

    text = STAT_FONT.render("Score : "+ str(score),1,(255,255,230))

    for pipe in pipes:
        pipe.draw(win)
    win.blit(text,(600,10))
    text = STAT_FONT.render("Generation : "+ str(gen-1),1,(255,255,230))
    win.blit(text,(10,10))

    base.draw(win)

    text = STAT_FONT.render("Alive : "+ str(alive),1,(255,255,230))
    win.blit(text,(10,600))

    reward.draw(win)

    for bird in birds:
        if bird.is_alive == 1:
            bird.draw(win)
    pygame.display.update()

#fitness function for all the genomes at once
def fitness_function(genomes,config):

    global GEN
    GEN += 1
    birds = []
    nets = []
    ge = []
    clock = pygame.time.Clock()


    for _,g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g,config)
        nets.append(net)
        birds.append(Bird(200,350))
        g.fitness = 0
        ge.append(g)


    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))

    pipes = [Pipe(900)]
    base = Base(700)
    reward = Reward(400,random.randrange(200,600))
    score = 0

    run = True
    reward_cnt = 2
    while run:
        clock.tick(40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds)>0 and score < 10:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].WIDTH:
                pipe_ind = 1
        else:
            break

        for bird in birds:
            bird.move()
            ge[birds.index(bird)].fitness += 0.1
            if bird.y > pipes[pipe_ind].height or bird.y > pipes[pipe_ind].bottom:
                ge[birds.index(bird)].fitness += 1
            # giving in the inputs
            output = nets[birds.index(bird)].activate((reward.x-bird.x,pipes[pipe_ind].x-bird.x,pipes[pipe_ind].height-bird.y,pipes[pipe_ind].bottom-bird.y,reward.y-bird.y))

            if output[0] > 0.5:
                bird.jump()
            if reward.collide(bird):
                ge[birds.index(bird)].fitness += 10000
        add_pipe = False
        rem = []
        for pipe in pipes:
            for bird in birds:
                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

                if not pipe.passed and pipe.x + pipe.WIDTH < bird.x:
                    pipe.passed = True
                    add_pipe = True



            if pipe.x + pipe.WIDTH < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe == True:
            score += 1
            for g in ge:
               g.fitness += 5

            pipes.append(Pipe(900))

        for r in rem:
            pipes.remove(r)
        for bird in birds:
            if bird.y + bird.img.get_height() >=  800 or bird.y < 0:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        reward.move()
        if reward.x + reward.img.get_width() < 0 and reward_cnt > 0:
            reward_cnt -= 1
            reward.x = 900
            reward.y = random.randrange(200,600)


        base.move()
        draw_window(win,birds,pipes,base,score,GEN,len(birds),reward)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome,neat.DefaultReproduction,neat.DefaultSpeciesSet,neat.DefaultStagnation,config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(fitness_function,15)

    visualize.plot_stats(stats)
    visualize.plot_species(stats)
    visualize.draw_net(config,winner, view=False, filename="xor2-all.gv")
    visualize.draw_net(config,winner, view=False, filename="xor2-enabled.gv", show_disabled=False)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir,"config-feedforward.txt")
    run(config_path)

