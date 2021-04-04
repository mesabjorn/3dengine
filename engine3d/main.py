import tkinter as tk
import time
import math
# import datetime
import functools
from copy import deepcopy, copy
# from tkinter import PhotoImage

# inspired on the cpp tutorail from https://www.youtube.com/watch?v=ih20l3pJoeU


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
    def __init__(self, x, y, z, w=None) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w if w else 1.0

    def aslist(self):
        return [self.x, self.y, self.z]

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"


class triangle:
    def __init__(self, p1, p2, p3) -> None:
        if(type(p1) == vec3d):
            self.vertices = [p1, p2, p3]
        else:
            self.vertices = [vec3d(*p1), vec3d(*p2), vec3d(*p3)]

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
        print(
            f"Loaded model {file} with {len(tris)} faces and {len(v)} vertices.")
        self.tris = tris

    def setAmbientColor(self, color: vec3d):
        self.ambientColor = color

    # def getAmbientColor(self):
    #     return self.ambientColor


class mat4x4:
    def __init__(self):
        self.mat = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]


def matmatmul(m1: mat4x4, m2: mat4x4) -> mat4x4:
    mout = mat4x4()
    for c in range(0, 4):
        for r in range(0, 4):
            mout.mat[r][c] = m1.mat[r][0] * m2.mat[0][c] + m1.mat[r][1] * \
                m2.mat[1][c] + m1.mat[r][2] * \
                m2.mat[2][c] + m1.mat[r][3] * m2.mat[3][c]
    return mout


def matPointAt(pos: vec3d, target: vec3d, up: vec3d) -> mat4x4:
    m = mat4x4()
    newForward = vec_normalize(vec_sub(target, pos))

    a = vec_mul(newForward, dot(up, newForward))
    newup = vec_normalize(vec_sub(up, a))

    newRight = cross(newup, newForward)

    matrix = mat4x4()
    matrix.mat[0][0] = newRight.x
    matrix.mat[1][0] = newup.x
    matrix.mat[2][0] = newForward.x
    matrix.mat[3][0] = pos.x

    matrix.mat[0][1] = newRight.y
    matrix.mat[1][1] = newup.y
    matrix.mat[2][1] = newForward.y
    matrix.mat[3][1] = pos.y

    matrix.mat[0][2] = newRight.z
    matrix.mat[1][2] = newup.z
    matrix.mat[2][2] = newForward.z
    matrix.mat[3][2] = pos.z

    matrix.mat[0][3] = 0
    matrix.mat[1][3] = 0
    matrix.mat[2][3] = 0
    matrix.mat[3][3] = 1

    return matrix


def matQuickInverse(m: mat4x4) -> mat4x4:
    matrix = mat4x4()
    matrix.mat[0][0] = m.mat[0][0]
    matrix.mat[1][0] = m.mat[0][1]
    matrix.mat[2][0] = m.mat[0][2]

    matrix.mat[0][1] = m.mat[1][0]
    matrix.mat[1][1] = m.mat[1][1]
    matrix.mat[2][1] = m.mat[1][2]

    matrix.mat[0][2] = m.mat[2][0]
    matrix.mat[1][2] = m.mat[2][1]
    matrix.mat[2][2] = m.mat[2][2]

    matrix.mat[0][3] = 0.0
    matrix.mat[1][3] = 0.0
    matrix.mat[2][3] = 0.0

    matrix.mat[3][0] = -(m.mat[3][0]*matrix.mat[0][0] + m.mat[3]
                         [1]*matrix.mat[1][0] + m.mat[3][2]*matrix.mat[2][0])
    matrix.mat[3][1] = -(m.mat[3][0]*matrix.mat[0][1] + m.mat[3]
                         [1]*matrix.mat[1][1] + m.mat[3][2]*matrix.mat[2][1])
    matrix.mat[3][2] = -(m.mat[3][0]*matrix.mat[0][2] + m.mat[3]
                         [1]*matrix.mat[1][2] + m.mat[3][2]*matrix.mat[2][2])
    matrix.mat[3][3] = 1.0

    return matrix


def MultiplyMatrixVector(i: vec3d, matrix: mat4x4) -> vec3d:
    output = vec3d(0.0, 0.0, 0.0, 0.0)
    m = matrix.mat
    output.x = i.x * m[0][0] + i.y * m[1][0] + i.z * m[2][0] + i.w*m[3][0]
    output.y = i.x * m[0][1] + i.y * m[1][1] + i.z * m[2][1] + i.w*m[3][1]
    output.z = i.x * m[0][2] + i.y * m[1][2] + i.z * m[2][2] + i.w*m[3][2]
    output.w = i.x * m[0][3] + i.y * m[1][3] + i.z * m[2][3] + i.w*m[3][3]

    # if(w != 0):
    #     output.x /= w
    #     output.y /= w
    #     output.z /= w

    return output


def makeMatRotationY(angleRad: float) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = math.cos(angleRad)
    m.mat[0][2] = math.sin(angleRad)
    m.mat[2][0] = -math.sin(angleRad)
    m.mat[1][1] = 1.0
    m.mat[2][2] = math.cos(angleRad)
    m.mat[3][3] = 1.0
    return m


def makeMatRotationZ(angleRad: float) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = math.cos(angleRad)
    m.mat[0][1] = math.sin(angleRad)
    m.mat[1][0] = -math.sin(angleRad)
    m.mat[1][1] = math.cos(angleRad)
    m.mat[2][2] = 1.0
    m.mat[3][3] = 1.0
    return m


def makeMatRotationX(angleRad: float) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = 1.0
    m.mat[1][1] = math.cos(angleRad)
    m.mat[1][2] = math.sin(angleRad)
    m.mat[2][1] = -math.sin(angleRad)
    m.mat[2][2] = math.cos(angleRad)
    m.mat[3][3] = 1.0
    return m


def makeMatTranslation(x, y, z) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = 1.0
    m.mat[1][1] = 1.0
    m.mat[2][2] = 1.0
    m.mat[3][3] = 1.0
    m.mat[3][0] = x
    m.mat[3][1] = y
    m.mat[3][2] = z
    return m


def makeMatProjection(fFov, aspectratio, fNear, fFar) -> mat4x4:
    # convert to degrees
    fFovRad = 1.0/math.tan(fFov*0.5/180.0*3.14159)

    m = mat4x4()
    m.mat[0][0] = aspectratio*fFovRad
    m.mat[1][1] = fFovRad
    m.mat[2][2] = fFar/(fFar-fNear)
    m.mat[3][2] = (-fFar*fNear)/(fFar-fNear)
    m.mat[2][3] = 1.0
    m.mat[3][3] = 0.0
    return m


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


def makeMatIdentity() -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = 1.0
    m.mat[1][1] = 1.0
    m.mat[2][2] = 1.0
    m.mat[3][3] = 1.0
    return m


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
        self.vLookDir = vec3d(0.0, 0.0, 0.0)

        self.vPointLight = vec3d(0.0, 0.0, -1.0)

        self.fillDetail = 5     # scanline resolution

        self.text_fps_id = self.create_text(
            50, 10, text=f"Press enter key to start", anchor="w", fill="#fff", font=("TKDefaultFont", 15))
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
                          scanlineY, width=f, **kwargs)

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
                          scanlineY, width=f, **kwargs)

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
            triTransformed = triangle([0, 0, 0], [0, 0, 0], [0, 0, 0])

            triTransformed.vertices[0] = MultiplyMatrixVector(
                t.vertices[0], self.matWorld)
            triTransformed.vertices[1] = MultiplyMatrixVector(
                t.vertices[1], self.matWorld)
            triTransformed.vertices[2] = MultiplyMatrixVector(
                t.vertices[2], self.matWorld)

            # tout0 = MultiplyMatrixVector(t.vertices[0], self.matRotZ)
            # tout1 = MultiplyMatrixVector(t.vertices[1], self.matRotZ)
            # tout2 = MultiplyMatrixVector(t.vertices[2], self.matRotZ)

            # triRotZ = triangle(
            #     tout0, tout1, tout2)

            # tout0 = MultiplyMatrixVector(triRotZ.vertices[0], self.matRotX)
            # tout1 = MultiplyMatrixVector(triRotZ.vertices[1], self.matRotX)
            # tout2 = MultiplyMatrixVector(triRotZ.vertices[2], self.matRotX)

            # triRotZX = triangle(
            #     tout0, tout1, tout2)

            # triRotZX.vertices[0].z += 20.0
            # triRotZX.vertices[1].z += 20.0
            # triRotZX.vertices[2].z += 20.0

            # get two edges on the triangle
            line1 = vec_sub(
                triTransformed.vertices[1], triTransformed.vertices[0])
            line2 = vec_sub(
                triTransformed.vertices[2], triTransformed.vertices[0])

            # cross product between line 1 and 2 => orthogonal vector
            normal = cross(line1, line2)
            normal = vec_normalize(normal)

            # get ray from triangle to camera
            vCameraRay = vec_sub(triTransformed.vertices[0], self.vCamera)

            # check if this face should be visualized
            if(dot(normal, vCameraRay) < 0.0):
                triProjected = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))
                # each triangle has 3 vertices
                # transform vertex coords to proj coords 3d->2d

                # compute correct color
                dp = dot(normal, vec_normalize(self.vPointLight))

                color = copy(self.m.ambientColor)

                color = vec_mul(color, dp)
                color.x = int(color.x)   # r channel
                color.y = int(color.y)   # g channel
                color.z = int(color.z)   # b channel

                color.x = max(color.x, 0)
                color.y = max(color.y, 0)
                color.z = max(color.z, 0)
                triProjected.color = color

                triViewed = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))

                triViewed.vertices[0] = MultiplyMatrixVector(
                    triTransformed.vertices[0], self.matView)
                triViewed.vertices[1] = MultiplyMatrixVector(
                    triTransformed.vertices[1], self.matView)
                triViewed.vertices[2] = MultiplyMatrixVector(
                    triTransformed.vertices[2], self.matView)
                # project triangle to 2d space
                triProjected.vertices[0] = MultiplyMatrixVector(
                    triViewed.vertices[0], self.matProj)
                triProjected.vertices[1] = MultiplyMatrixVector(
                    triViewed.vertices[1], self.matProj)
                triProjected.vertices[2] = MultiplyMatrixVector(
                    triViewed.vertices[2], self.matProj)

                triProjected.vertices[0] = vec_div(
                    triProjected.vertices[0], triProjected.vertices[0].w)
                triProjected.vertices[1] = vec_div(
                    triProjected.vertices[1], triProjected.vertices[1].w)
                triProjected.vertices[2] = vec_div(
                    triProjected.vertices[2], triProjected.vertices[2].w)

                # put it into view
                vOffsetView = vec3d(1, 1, 0)
                triProjected.vertices[0] = vec_add(
                    triProjected.vertices[0], vOffsetView)
                triProjected.vertices[1] = vec_add(
                    triProjected.vertices[1], vOffsetView)
                triProjected.vertices[2] = vec_add(
                    triProjected.vertices[2], vOffsetView)

                # scale into view
                triProjected.vertices[0].x *= self.hWidth
                triProjected.vertices[0].y *= self.hHeight
                triProjected.vertices[1].x *= self.hWidth
                triProjected.vertices[1].y *= self.hHeight
                triProjected.vertices[2].x *= self.hWidth
                triProjected.vertices[2].y *= self.hHeight

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
        self.matProj = makeMatProjection(fFov, self.aspectratio, fNear, fFar)

    def perform_actions(self):
        # self.draw()
        t1 = time.perf_counter()
        self.delete(tk.ALL)
        theta = 0  # t1*0.5

        self.matRotZ = makeMatRotationZ(theta)
        self.matRotX = makeMatRotationX(theta)
        self.matRotY = makeMatRotationY(theta)

        self.matTrans = makeMatTranslation(0, 0, 5.0)

        self.matWorld = makeMatIdentity()
        self.matWorld = matmatmul(self.matRotY, self.matRotY)
        self.matWorld = matmatmul(self.matRotY, self.matRotZ)
        self.matWorld = matmatmul(self.matWorld, self.matTrans)

        self.vLookDir = vec3d(0, 0, 1)
        vUp = vec3d(0, 1, 0)
        vTarget = vec_add(self.vCamera, self.vLookDir)

        matCamera = matPointAt(self.vCamera, vTarget, vUp)
        self.matView = matQuickInverse(matCamera)

        self.drawmeshes()

        t2 = time.perf_counter()-t1             # frame draw time

        self.text_fps_id = self.create_text(
            0, 10, text=f"{1/t2:3.0f} fps", anchor="w", fill="#fff", font=("TKDefaultFont", 12))
        self.after(max(1, int(t2*1000)), self.perform_actions)
        # self.update_idletasks()

    def on_key_press(self, e):
        # model = self.create_cube()
        print(e)
        if(e.keycode == 13):
            model = mesh()
            model.loadmodelfromfile("./engine3d/models/axis.obj")
            model.ambientColor = vec3d(64, 224, 208)
            self.addmodeltoscene(model)
            return

        if(e.keycode == 87):
            self.vCamera.z += 1
        elif(e.keycode == 83):
            self.vCamera.z -= 1
        elif(e.keycode == 68):
            # d
            self.vCamera.x += 1
        elif(e.keycode == 65):
            # a
            self.vCamera.x -= 1

        # self.addmodeltoscene(model)
        # for x in range(4 * self.width):
        #     y = int(self.height/2 + self.height/4 * math.sin(x/80.0))
        #     self.img.put("#ffffff", (x//4, y))

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
