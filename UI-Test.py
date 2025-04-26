import salabim as sim

env = sim.Environment()

# kijk naar trjacectory
class X(sim.Component):
    def animation_objects1(self):
        an1 = env.AnimateImage("https://salabim.org/bird.gif", animation_repeat=True, width=50, offsety=-15)
        an2 = env.AnimateText(text=f"{self.sequence_number()}", offsetx=15, offsety=-25, fontsize=13)
        return 50, 50, an1, an2

    def process(self):
        self.enter(env.q)
        self.hold(env.Uniform(5))
        self.leave(env.q)

env.speed(3)
env.background_color(("#eeffcc"))
env.width(1000, True)
env.height(700)
env.animate(True)
env.AnimateImage("https://salabim.org/bird.gif", animation_repeat=True, width=150, x=lambda t: 1000 - 30 * t, y=150)
env.AnimateImage("https://salabim.org/bird.gif", animation_repeat=True, width=300, x=lambda t: 1000 - 60 * t, y=220)
env.AnimateImage(
    "https://salabim.org/bird.gif",
    animation_repeat=True,
    width=100,
    animation_speed=1.5,
    x=lambda t: 0 + 100 * (t - 25),
    y=350,
    animation_start=25,
    flip_horizontal=True,
)
env.AnimateImage("https://salabim.org/bird.gif", animation_repeat=True, width=240, animation_speed=0.5, x=lambda t: 1000 - 50 * t, y=380)
env.AnimateImage("https://salabim.org/bird.gif", animation_repeat=True, width=250, animation_speed=1.3, x=lambda t: 1000 - 40 * t, y=480)

env.q = env.Queue("queue")
env.q.animate(x=700, y=50, direction="w")
env.ComponentGenerator(X, iat=env.Exponential(1.5))
env.run()