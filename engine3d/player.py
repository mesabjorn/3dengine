from veclib import vec3d, mat4x4, triangle, mesh, rgbToHex, matmatmul, matPointAt, matQuickInverse, mulVecMat, triangleClipAgainstPlane, makeMatRotationX, makeMatRotationY, makeMatRotationZ, makeMatTranslation, dot, cross, makeMatProjection, vec_add, vec_sub, vec_mul, vec_div, vec_len, vec_normalize, makeMatIdentity, sort_triangles_by_z
import functools
from copy import deepcopy, copy
import math

import random


def makeScaleMat(sx, sy, sz):
    m = mat4x4()
    m.mat[0][0] = sx
    m.mat[1][1] = sy
    m.mat[2][2] = sz
    m.mat[3][3] = 1
    return m


class SceneObject:
    def __init__(self, file=None, vPos=(0, 0, 0), vRot=(0, 0, 0), vScale=(1, 1, 1)) -> None:
        self.vPos = vec3d(*vPos)
        self.initPos = vec3d(*vPos)
        self.scaleMat = makeScaleMat(*vScale)
        self.matTrans = makeMatTranslation(*vPos)
        self.rotate = False

        self.myupdatefunction = None
        if(file):
            self.mesh = mesh()
            self.mesh.loadmodelfromfile(f"./engine3d/models/{file}")
            self.ambientColor = vec3d(255, 255, 255)

    def draw(self, tick, engine):
        # called after update
        trianglesToRaster = []

        for t in self.mesh.tris:
            triTransformed = triangle([0, 0, 0], [0, 0, 0], [0, 0, 0])

            triTransformed.vertices[0] = mulVecMat(
                t.vertices[0], engine.matWorld)
            triTransformed.vertices[1] = mulVecMat(
                t.vertices[1], engine.matWorld)
            triTransformed.vertices[2] = mulVecMat(
                t.vertices[2], engine.matWorld)

            # use each sceneobjects cusom translation
            triTransformed.vertices[0] = vec_add(
                triTransformed.vertices[0], self.vPos)
            triTransformed.vertices[1] = vec_add(
                triTransformed.vertices[1], self.vPos)
            triTransformed.vertices[2] = vec_add(
                triTransformed.vertices[2], self.vPos)

            # scale object
            triTransformed.vertices[0] = mulVecMat(
                triTransformed.vertices[0], self.scaleMat)
            triTransformed.vertices[1] = mulVecMat(
                triTransformed.vertices[1], self.scaleMat)
            triTransformed.vertices[2] = mulVecMat(
                triTransformed.vertices[2], self.scaleMat)

            if(self.rotate):
                rotZ = makeMatRotationY(tick)
                triTransformed.vertices[0] = mulVecMat(
                    triTransformed.vertices[0], rotZ)
                triTransformed.vertices[1] = mulVecMat(
                    triTransformed.vertices[1], rotZ)
                triTransformed.vertices[2] = mulVecMat(
                    triTransformed.vertices[2], rotZ)

            # get two edges on the triangle
            line1 = vec_sub(
                triTransformed.vertices[1], triTransformed.vertices[0])
            line2 = vec_sub(
                triTransformed.vertices[2], triTransformed.vertices[0])

            # cross product between line 1 and 2 => orthogonal vector
            normal = cross(line1, line2)
            normal = vec_normalize(normal)

            # get ray from triangle to camera
            vCameraRay = vec_sub(
                triTransformed.vertices[0], engine.Player.Camera.vPos)

            # check if this face should be visualized
            if(dot(normal, vCameraRay) < 0.0):
                triProjected = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))
                # each triangle has 3 vertices
                # transform vertex coords to proj coords 3d->2d

                # compute correct color
                dp = dot(normal, vec_normalize(engine.vPointLight))
                # dp = 1
                color = copy(self.ambientColor)

                color = vec_mul(color, dp)
                color.x = int(color.x)   # r channel
                color.y = int(color.y)   # g channel
                color.z = int(color.z)   # b channel

                # color.x = max(color.x, 0)
                # color.y = max(color.y, 0)
                # color.z = max(color.z, 0)

                triViewed = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))

                triViewed.vertices[0] = mulVecMat(
                    triTransformed.vertices[0], engine.Player.Camera.matView)
                triViewed.vertices[1] = mulVecMat(
                    triTransformed.vertices[1], engine.Player.Camera.matView)
                triViewed.vertices[2] = mulVecMat(
                    triTransformed.vertices[2], engine.Player.Camera.matView)

                triViewed.color = color

                nClippedTris = triangleClipAgainstPlane(
                    vec3d(0, 0, .1), vec3d(0, 0, 1.0), triViewed)

                clippedTriangles = []
                if(nClippedTris[0] >= 1):
                    clippedTriangles = nClippedTris[1:]
                # print(f"len clipped tris:{nClippedTris[0]}")

                for clippedTriangle in clippedTriangles:
                    # project triangle to 2d space
                    triProjected = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))

                    triProjected.vertices[0] = mulVecMat(
                        clippedTriangle.vertices[0], engine.Player.Camera.matProj)
                    triProjected.vertices[1] = mulVecMat(
                        clippedTriangle.vertices[1], engine.Player.Camera.matProj)
                    triProjected.vertices[2] = mulVecMat(
                        clippedTriangle.vertices[2], engine.Player.Camera.matProj)

                    triProjected.vertices[0] = vec_div(
                        triProjected.vertices[0], triProjected.vertices[0].w)
                    triProjected.vertices[1] = vec_div(
                        triProjected.vertices[1], triProjected.vertices[1].w)
                    triProjected.vertices[2] = vec_div(
                        triProjected.vertices[2], triProjected.vertices[2].w)

                    triProjected.vertices[0].x *= -1
                    triProjected.vertices[0].y *= -1
                    triProjected.vertices[1].x *= -1
                    triProjected.vertices[1].y *= -1
                    triProjected.vertices[2].x *= -1
                    triProjected.vertices[2].y *= -1

                    # put it into view (offset it into x,y direction)
                    vOffsetView = vec3d(1, 1, 0)
                    triProjected.vertices[0] = vec_add(
                        triProjected.vertices[0], vOffsetView)
                    triProjected.vertices[1] = vec_add(
                        triProjected.vertices[1], vOffsetView)
                    triProjected.vertices[2] = vec_add(
                        triProjected.vertices[2], vOffsetView)

                    # scale into view
                    triProjected.vertices[0].x *= engine.hWidth
                    triProjected.vertices[0].y *= engine.hHeight
                    triProjected.vertices[1].x *= engine.hWidth
                    triProjected.vertices[1].y *= engine.hHeight
                    triProjected.vertices[2].x *= engine.hWidth
                    triProjected.vertices[2].y *= engine.hHeight

                    # triProjected.color = copy(triViewed.color)
                    triProjected.color = clippedTriangle.color

                    trianglesToRaster.append(triProjected)

        # sort triangles in z axis for painters rendering
        trianglesToRaster = sorted(
            trianglesToRaster, key=functools.cmp_to_key(sort_triangles_by_z))

        for t in trianglesToRaster:
            listTriangles = []
            listTriangles.append(t)
            nNewTriangles = 1
            for p in range(0, 4):
                nTrisToAdd = 0
                while nNewTriangles > 0:
                    test = listTriangles[0]
                    del listTriangles[0]
                    nNewTriangles -= 1

                    if(p == 0):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(0, 0, 0), vec3d(0, 1, 0), test)
                    elif(p == 1):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(0, engine.height-1, 0), vec3d(0, -1, 0), test)
                    elif(p == 2):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(0, 0, 0), vec3d(1, 0, 0), test)
                    elif(p == 3):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(engine.width-1, 0, 0), vec3d(-1, 0, 0), test)

                    if(nTrisToAdd[0] >= 1):
                        for n in nTrisToAdd[1:]:
                            listTriangles.append(n)
                nNewTriangles = len(listTriangles)

            for t in listTriangles:
                # t.color = vec3d(255, 255, 255)
                engine.create_polygon(t.vertices[0].x, t.vertices[0].y, t.vertices[1].x,
                                      t.vertices[1].y, t.vertices[2].x, t.vertices[2].y, fill=rgbToHex(t.color), tag="triangle")

                # self.drawtriangle(t, fill="white")      # enable wireframe mode

    def update(self, t):
        if(self.myupdatefunction):
            self.myupdatefunction(self, t)

    def setBehavior(self, behaviorfunc):
        self.myupdatefunction = behaviorfunc

    def bounce(self, t):
        self.vPos.y = self.initPos.y+math.sin(t)
        # print(self.vPos.y)


class Camera(SceneObject):
    def __init__(self, vPos) -> None:
        super().__init__(None, vPos)
        self.yaw = 0
        self.pitch = 0
        self.roll = 0

        # self.vCamera = self.vPos
        self.vLookDir = vec3d(0.0, 0.0, 0.0)
        # self.setup_viewport()

    def setup_viewport(self, aspect_ratio):
        fNear = 0.1
        fFar = 1000.0
        fFov = 90.0         # degrees FOV
        self.matProj = makeMatProjection(fFov, aspect_ratio, fNear, fFar)

    def setCamera(self):
        # self.vLookDir = vec3d(0, 0, 1)
        vUp = vec3d(0, -1, 0)
        # vTarget = vec_add(self.vCamera, self.vLookDir)
        vTarget = vec3d(0, 0, 1)
        matCameraRotX = makeMatRotationX(self.pitch)
        matCameraRotY = makeMatRotationY(self.yaw)
        matCameraRotXY = matmatmul(matCameraRotX, matCameraRotY)
        # matCameraRot = matmatmul(matCameraRot, makeMatRotationX(self.pitch))
        self.vLookDir = mulVecMat(vTarget, matCameraRotXY)
        # self.vLookDir = mulVecMat(self.vLookDir, matCameraRotX)
        vTarget = vec_add(self.vPos, self.vLookDir)

        matCamera = matPointAt(self.vPos, vTarget, vUp)
        self.matView = matQuickInverse(matCamera)


class Player(SceneObject):
    def __init__(self, file, vPos) -> None:
        super().__init__(file, vPos)

        self.Camera = Camera(vPos)
        self.Camera2 = Camera((-74, -102, -86))
