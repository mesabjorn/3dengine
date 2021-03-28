import tkinter as tk
import time
import math

MOVE_INCREMENT = 20
moves_per_second = 15
GAME_SPEED = 1000//moves_per_second


class vec3d:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def aslist(self):
        return [self.x, self.y, self.z]


class triangle:
    def __init__(self, p1, p2, p3) -> None:
        self.vertices = [vec3d(*p1), vec3d(*p2), vec3d(*p3)]


class mesh:
    def __init__(self, *args):
        self.tris = [*args]
        print(self.tris)


class mat4x4:
    def __init__(self):
        self.mat = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]


def MultiplyMatrixVector(i, matrix):
    output = vec3d(0.0, 0.0, 0.0)
    m = matrix.mat
    output.x = i.x * m[0][0] + i.y * m[1][0] + i.z*m[2][0] + m[3][0]
    output.y = i.x * m[0][1] + i.y * m[1][1] + i.z*m[2][1] + m[3][1]
    output.z = i.x * m[0][2] + i.y * m[1][2] + i.z*m[2][2] + m[3][2]

    w = i.x * m[0][3] + i.y * m[1][3] + i.z * m[2][3] + m[3][3]

    if(w != 0):
        output.x /= w
        output.y /= w
        output.z /= w

    return output


class Engine(tk.Canvas):
    def __init__(self, width=800, height=600):
        super().__init__(width=800, height=600, background="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.aspectratio = self.height/self.width

        # right facing snake, 3 body elements, 20px width
        self.bind_all("<Key>", self.on_key_press)

        self.after(GAME_SPEED, self.perform_actions)

    def drawline(self, x1, y1, x2, y2):
        self.create_line(x1, y1, x2, y2, fill="white")

    def drawtriangle(self, tri):
        # draw a triangle in clockwise fashion
        # each triangle has 3 vertices
        self.drawline(tri.vertices[0].x, tri.vertices[0].y,
                      tri.vertices[1].x, tri.vertices[1].y)
        self.drawline(tri.vertices[1].x, tri.vertices[1].y,
                      tri.vertices[2].x, tri.vertices[2].y)
        self.drawline(tri.vertices[2].x, tri.vertices[2].y,
                      tri.vertices[0].x, tri.vertices[0].y)

    def drawmesh(self, m):
        # for t in m.tris:
        for i in range(0, len(m.tris)):
            t = m.tris[i]
            # each triangle has 3 vertices
            # transform vertex coords to proj coords
            tout0 = MultiplyMatrixVector(t.vertices[0], self.matProj)
            tout1 = MultiplyMatrixVector(t.vertices[1], self.matProj)
            tout2 = MultiplyMatrixVector(t.vertices[2], self.matProj)

            # build a triangle in transformed coords
            triProjected = triangle(
                tout0.aslist(), tout1.aslist(), tout2.aslist())

            triProjected.vertices[0].x += 1
            triProjected.vertices[0].y += 1

            triProjected.vertices[1].x += 1
            triProjected.vertices[1].y += 1

            triProjected.vertices[2].x += 1
            triProjected.vertices[2].y += 1

            triProjected.vertices[0].x *= 0.5*self.width
            triProjected.vertices[0].y *= 0.5*self.height
            triProjected.vertices[1].x *= 0.5*self.width
            triProjected.vertices[1].y *= 0.5*self.height
            triProjected.vertices[2].x *= 0.5*self.width
            triProjected.vertices[2].y *= 0.5*self.height

            # triProjected.vertices[0].y = self.height-triProjected.vertices[0].y
            # triProjected.vertices[1].y = self.height-triProjected.vertices[1].y
            # triProjected.vertices[2].y = self.height-triProjected.vertices[2].y

            # and draw it
            self.drawtriangle(triProjected)
            # if(i == 0):
            #     break

    def draw(self):
        pass

    def perform_actions(self):
        self.draw()
        self.after(GAME_SPEED, self.perform_actions)

    def on_key_press(self, e):
        new_direction = e.keysym
        # self.drawline(100, 100, 200, 200)
        # t = triangle((100, 50), (100, 100), (150, 100))
        # t2 = triangle((100, 50), (150, 100), (150, 50))

        # south (facing us)
        t0 = triangle((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
        t1 = triangle((0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0))

        # east
        t2 = triangle((1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0))
        t3 = triangle((1.0, 0.0, 0.0), (1.0, 1.0, 1.0), (1.0, 0.0, 1.0))

        # north
        t4 = triangle((1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0))
        t5 = triangle((1.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.0, 0.0, 1.0))

        # west
        t6 = triangle((0.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.0, 1.0, 0.0))
        t7 = triangle((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0))

        # top
        t8 = triangle((0.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 1.0, 1.0))
        t9 = triangle((0.0, 1.0, 0.0), (1.0, 1.0, 1.0), (1.0, 1.0, 0.0))

        # bottom
        t10 = triangle((1.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        t11 = triangle((1.0, 0.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))

        fNear = 0.1
        fFar = 1000.0
        fFov = 90.0
        fFovRad = 1.0/math.tan(fFov*0.5/180.0*3.14159)

        self.matProj = mat4x4()
        self.matProj.mat[0][0] = self.aspectratio*fFovRad
        self.matProj.mat[1][1] = fFovRad
        self.matProj.mat[2][2] = fFar/(fFar-fNear)
        self.matProj.mat[3][2] = (-fFar*fNear)/(fFar-fNear)
        self.matProj.mat[2][2] = 1.0
        self.matProj.mat[3][3] = 0.0

        print(self.matProj.mat)
        m = mesh(t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11)
        self.drawmesh(m)


root = tk.Tk()
root.title("3d engine")
root.resizable(False, False)

board = Engine()
board.pack()

height = 800

# board.drawline(400, height-0, 400, 400)
# board.drawline(400, 600, 700, 300)

# m = mat4x4()
# print(m.mat[3][3])


root.mainloop()
