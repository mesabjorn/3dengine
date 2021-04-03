import tkinter as tk
import time
import math
import datetime
import functools
# inspired on the cpp tutorail from https://www.youtube.com/watch?v=ih20l3pJoeU
from copy import deepcopy

from tkinter import PhotoImage


MOVE_INCREMENT = 20
moves_per_second = 15
GAME_SPEED = 1000//moves_per_second


def sort_triangles_by_z(t1, t2):
    z1 = (t1.vertices[0].z+t1.vertices[1].z+t1.vertices[2].z)/3.0
    z2 = (t2.vertices[0].z+t2.vertices[1].z+t2.vertices[2].z)/3.0
    return z2 - z1


class Zbuffer:
    def __init__(self, width, height):
        self.buffer = []
        self.width = width
        self.height = height
        self.clear()

    def clear(self):
        for _ in range(0, self.width*self.height):
            self.buffer.append(math.inf)

    def at(self, x, y):
        return self.buffer[y*self.width+x]

    def testAndSet(self, x, y, depth):
        d = self.at(x, y)
        if(depth < d):
            d = depth
            return True
        return False


class vec3d:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def aslist(self):
        return [self.x, self.y, self.z]

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"


class triangle:
    def __init__(self, p1, p2, p3) -> None:
        if(type(p1) == vec3d):
            self.vertices = (p1, p2, p3)
        else:
            self.vertices = (vec3d(*p1), vec3d(*p2), vec3d(*p3))

        self.color = vec3d(255, 255, 255)


class mesh:
    ambientColor = vec3d(255, 255, 255)

    def __init__(self, *args):
        self.tris = [*args]

        # print(self.tris)

    def loadmodelfromfile(self, file):
        # load .obj file
        with open(file, "r") as f:
            v = []
            tris = []
            while(True):
                l = f.readline().strip()
                if(len(l) == 0):
                    break
                if l[0] == "v":
                    # is vertex
                    data = list(map(lambda x: float(x), l[2:].split(" ")))
                    v.append(vec3d(data[0], data[1], data[2]))
                elif l[0] == "f":
                    # isface
                    data = list(map(lambda x: int(x), l[2:].split(" ")))
                    t = triangle(v[data[0]-1], v[data[1]-1], v[data[2]-1])
                    tris.append(t)
        self.tris = tris

    def setAmbientColor(self, color: vec3d):
        self.ambientColor = color

    # def getAmbientColor(self):
    #     return self.ambientColor


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


def vec_add(v1: vec3d, v2: vec3d) -> vec3d:
    return vec3d(v1.x+v2.x, v1.y+v2.y, v1.z+v2.z)


def vec_sub(v1: vec3d, v2: vec3d) -> vec3d:
    return vec3d(v1.x-v2.x, v1.y-v2.y, v1.z-v2.z)


def vec_mul(v1: vec3d, k: float) -> vec3d:
    return vec3d(v1.x*k, v1.y*k, v1.z*k)


def vec_div(v1: vec3d, k: float) -> vec3d:
    return vec3d(v1.x/k, v1.y/k, v1.z/k)


def dot(v1: vec3d, v2: vec3d) -> float:
    return v1.x*v2.x+v1.y*v2.y+v1.z*v2.z


def cross(v1: vec3d, v2: vec3d) -> vec3d:
    return vec3d(v1.y*v2.z-v1.z*v2.y,
                 v1.z*v2.x-v1.x*v2.z,
                 v1.x*v2.y-v1.y*v2.x)


def vec_len(v: vec3d) -> vec3d:
    return math.sqrt(dot(v, v))


def vec_normalize(v: vec3d) -> vec3d:
    l = vec_len(v)
    return vec3d(v.x/l, v.y/l, v.z/l)


class Engine(tk.Canvas):
    def __init__(self, width=800, height=600):
        super().__init__(width=800, height=600, background="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.aspectratio = self.height/self.width

        # half width and height
        self.hWidth = width*0.5
        self.hHeight = height*0.5

        # self.img = PhotoImage(width=width, height=height)
        # self.create_image((width/2, height/2),
        #                   image=self.img, state="normal")

        # self.ZBuffer = Zbuffer(width, height)

        self.tstart = time.perf_counter()

        self.vCamera = vec3d(0.0, 0.0, 0.0)
        self.vPointLight = vec3d(0.0, 0.0, -1.0)

        self.fillDetail = 1     # scanline resolution

        self.text_fps_id = self.create_text(
            50, 10, text=f"Press any key", anchor="w", fill="#fff", font=("TKDefaultFont", 15))
        # right facing snake, 3 body elements, 20px width
        self.bind_all("<Key>", self.on_key_press)

        self.setup_viewport()

        self.matRotZ = mat4x4()
        self.matRotX = mat4x4()

        # self.after(GAME_SPEED, self.perform_actions)

    def drawline(self, x1, y1, x2, y2, **kwargs):
        self.create_line(x1, y1, x2, y2, **kwargs)

    def drawtriangle(self, tri, **kwargs):
        # draw a triangle in clockwise fashion
        # each triangle has 3 vertices
        self.drawline(tri.vertices[0].x, tri.vertices[0].y,
                      tri.vertices[1].x, tri.vertices[1].y, **kwargs)
        self.drawline(tri.vertices[1].x, tri.vertices[1].y,
                      tri.vertices[2].x, tri.vertices[2].y, **kwargs)
        self.drawline(tri.vertices[2].x, tri.vertices[2].y,
                      tri.vertices[0].x, tri.vertices[0].y, **kwargs)

    def fillBottomFlatTriangle(self, v1, v2, v3, **kwargs):
        # v1 = tri.vertices[0]
        # v2 = tri.vertices[1]
        # v3 = tri.vertices[2]

        f = self.fillDetail

        invSlope1 = f*(v3.x - v2.x) / (v3.y-v2.y)
        invSlope2 = f*(v3.x - v1.x) / (v3.y-v1.y)

        curx1 = v3.x
        curx2 = v3.x
        scanlineY = v3.y
        while(scanlineY <= v1.y):
            self.drawline(curx1, scanlineY, curx2,
                          scanlineY, width=2, **kwargs)

            curx1 += invSlope1
            curx2 += invSlope2
            scanlineY += f

    def fillTopFlatTriangle(self, v1, v2, v3, **kwargs):
        f = self.fillDetail
        invSlope1 = f*(v1.x - v2.x) / (v1.y-v2.y)
        invSlope2 = f*(v1.x - v3.x) / (v1.y-v3.y)

        curx1 = v1.x
        curx2 = v1.x
        scanlineY = v1.y
        while(scanlineY >= v3.y):
            self.drawline(curx1, scanlineY, curx2,
                          scanlineY, width=2, **kwargs)

            curx1 -= invSlope1
            curx2 -= invSlope2
            scanlineY -= f

    def fillTriangle_new(self, tri, **kwargs):
        v3, v2, v1 = sorted(tri.vertices, key=lambda v: v.y, reverse=False)

        # genericcase!
        v4 = vec3d(v3.x+(v2.y-v3.y)/(v1.y-v3.y)*(v1.x-v3.x), v2.y, 0)
        self.fillTopFlatTriangle(v1, v2, v4,  **kwargs)
        self.fillBottomFlatTriangle(v2, v4, v3,  **kwargs)

    def fillTriangle(self, tri):
        steps = 20

        # sort vertices by y position
        ys = sorted(tri.vertices, key=lambda v: v.y, reverse=True)

        p1 = ys[0]
        p2 = ys[1]
        p3 = ys[2]
        Q = p2.y

        x0 = p1.x
        y0 = p1.y
        for i in range(1, steps+1, 1):
            t = i/steps
            # print(t)
            ax = x0+((p3.x-p1.x)*t)
            ay = y0+((p3.y-p1.y)*t)

            bx = x0+((p2.x-p1.x)*t)
            by = y0+((p2.y-p1.y)*t)

            self.create_line(ax, ay, bx, by, fill="#FFF", width=5)
            # print(by)
            # print(
            #     f"board.create_line({int(ax)},{int(ay)},{int(bx)},{int(by)}, fill='white')")
            # if(ay < Q):
            #     break

    def drawmeshes(self):
        # for t in m.tris:
        trianglesToRaster = []
        for t in self.m.tris:

            tout0 = MultiplyMatrixVector(t.vertices[0], self.matRotZ)
            tout1 = MultiplyMatrixVector(t.vertices[1], self.matRotZ)
            tout2 = MultiplyMatrixVector(t.vertices[2], self.matRotZ)

            triRotZ = triangle(
                tout0, tout1, tout2)

            tout0 = MultiplyMatrixVector(triRotZ.vertices[0], self.matRotX)
            tout1 = MultiplyMatrixVector(triRotZ.vertices[1], self.matRotX)
            tout2 = MultiplyMatrixVector(triRotZ.vertices[2], self.matRotX)

            triRotZX = triangle(
                tout0, tout1, tout2)

            triRotZX.vertices[0].z += 10.0
            triRotZX.vertices[1].z += 10.0
            triRotZX.vertices[2].z += 10.0

            # get two edges on the triangle
            line1 = vec_sub(triRotZX.vertices[1], triRotZX.vertices[0])
            line2 = vec_sub(triRotZX.vertices[2], triRotZX.vertices[0])

            # cross product between line 1 and 2 => orthogonal vector
            normal = cross(line1, line2)

            # normalize normal
            normal = vec_normalize(normal)

            # get dotproduct between vertex-camera direction and face normal
            dotproduct = dot(normal, vec_sub(
                triRotZX.vertices[0], self.vCamera))

            # check if this face should be visualized
            if(dotproduct < 0.0):
                # each triangle has 3 vertices
                # transform vertex coords to proj coords 3d->2d

                # compute correct color
                dp = dot(normal, vec_normalize(self.vPointLight))

                color = deepcopy(self.m.ambientColor)

                color = vec_mul(color, dp)
                color.x = int(color.x)   # r channel
                color.y = int(color.y)   # g channel
                color.z = int(color.z)   # b channel

                color.x = max(color.x, 0)
                color.y = max(color.y, 0)
                color.z = max(color.z, 0)

                tout0 = MultiplyMatrixVector(
                    triRotZX.vertices[0], self.matProj)
                tout1 = MultiplyMatrixVector(
                    triRotZX.vertices[1], self.matProj)
                tout2 = MultiplyMatrixVector(
                    triRotZX.vertices[2], self.matProj)

                # build a triangle in transformed coords
                triProjected = triangle(
                    tout0, tout1, tout2)

                triProjected.vertices[0].x += 1
                triProjected.vertices[0].y += 1

                triProjected.vertices[1].x += 1
                triProjected.vertices[1].y += 1

                triProjected.vertices[2].x += 1
                triProjected.vertices[2].y += 1

                # scale into view
                triProjected.vertices[0].x *= self.hWidth
                triProjected.vertices[0].y *= self.hHeight
                triProjected.vertices[1].x *= self.hWidth
                triProjected.vertices[1].y *= self.hHeight
                triProjected.vertices[2].x *= self.hWidth
                triProjected.vertices[2].y *= self.hHeight

                triProjected.color = color
                trianglesToRaster.append(triProjected)

        # sort triangles in z axis for painters rendering
        trianglesToRaster = sorted(
            trianglesToRaster, key=functools.cmp_to_key(sort_triangles_by_z))

        for t in trianglesToRaster:

            self.create_polygon(t.vertices[0].x, t.vertices[0].y, t.vertices[1].x,
                                t.vertices[1].y, t.vertices[2].x, t.vertices[2].y, fill=f"#{t.color.x:02x}{t.color.y:02x}{t.color.z:02x}", tag="triangle")

    def draw(self):
        pass

    def setup_viewport(self):
        fNear = 0.1
        fFar = 1000.0
        fFov = 90.0         # degrees FOV
        # convert to degrees
        fFovRad = 1.0/math.tan(fFov*0.5/180.0*3.14159)

        self.matProj = mat4x4()
        self.matProj.mat[0][0] = self.aspectratio*fFovRad
        self.matProj.mat[1][1] = fFovRad
        self.matProj.mat[2][2] = fFar/(fFar-fNear)
        self.matProj.mat[3][2] = (-fFar*fNear)/(fFar-fNear)
        self.matProj.mat[2][3] = 1.0
        self.matProj.mat[3][3] = 0.0

    def perform_actions(self):
        # self.draw()
        t1 = time.perf_counter()
        self.delete(tk.ALL)
        theta = (t1-self.tstart)

        # compute rotation of Z
        self.matRotZ.mat[0][0] = math.cos(theta*0.5)
        self.matRotZ.mat[0][1] = math.sin(theta*0.5)
        self.matRotZ.mat[1][0] = -math.sin(theta*0.5)
        self.matRotZ.mat[1][1] = math.cos(theta*0.5)
        self.matRotZ.mat[2][2] = 1.0
        self.matRotZ.mat[3][3] = 1.0

        # compute rotation of X
        self.matRotX.mat[0][0] = 1.0
        self.matRotX.mat[1][1] = math.cos(theta*0.5)
        self.matRotX.mat[1][2] = math.sin(theta*0.5)
        self.matRotX.mat[2][1] = -math.sin(theta*0.5)
        self.matRotX.mat[2][2] = math.cos(theta*0.5)
        self.matRotX.mat[3][3] = 1.0

        self.drawmeshes()

        t2 = time.perf_counter()-t1             # frame draw time
        self.text_fps_id = self.create_text(
            0, 10, text=f"fps = {1/t2:.3f}", anchor="w", fill="#fff", font=("TKDefaultFont", 15))

        self.after(max(1, int(t2*1000)), self.perform_actions)
        # self.update_idletasks()

    def on_key_press(self, e):
        # model = self.create_cube()

        model = mesh()
        model.loadmodelfromfile("./engine3d/models/test.obj")
        model.ambientColor = vec3d(64, 224, 208)

        # self.addmodeltoscene(model)
        # for x in range(4 * self.width):
        #     y = int(self.height/2 + self.height/4 * math.sin(x/80.0))
        #     self.img.put("#ffffff", (x//4, y))

        self.addmodeltoscene(model)

    def addmodeltoscene(self, model):
        self.m = model
        self.perform_actions()

    def create_cube(self):

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

        # print(self.matProj.mat)
        return mesh(t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11)
        # self.perform_actions()


root = tk.Tk()
root.title("3d engine")
root.resizable(False, False)

board = Engine()
board.pack()

# board.drawline(100, 100, 200, 200)

# board.create_line(100, 100, 200, 200, arrow=tk.LAST, fill="#FFF")

# flat top
# a = (100, 200, 100)
# b = (50, 100, 100)
# c = (150, 100, 100)
# t = triangle(a, b, c)
# board.drawtriangle(t)
# board.fillTriangle_new(t)

# a = (300, 200, 100)
# b = (400, 100, 100)
# c = (500, 250, 100)
# t = triangle(a, b, c)
# board.drawtriangle(t)
# board.fillTriangle_new(t)

# a = (400, 400, 100)
# b = (450, 200, 100)
# c = (700, 100, 100)
# t = triangle(a, b, c)
# board.drawtriangle(t)
# board.fillTriangle_new(t)

root.mainloop()
