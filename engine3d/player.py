from veclib import vec3d, mat4x4, triangle, mesh, rgbToHex, matmatmul, matPointAt, matQuickInverse, mulVecMat, triangleClipAgainstPlane, makeMatRotationX, makeMatRotationY, makeMatRotationZ, makeMatTranslation, dot, cross, makeMatProjection, vec_add, vec_sub, vec_mul, vec_div, vec_len, vec_normalize, makeMatIdentity, sort_triangles_by_z


class SceneObject:
    def __init__(self, x, y, z, file=None) -> None:
        self.vPos = vec3d(x, y, z)
        self.matTrans = makeMatTranslation(x, y, z)
        self.rotate = False
        if(file):
            self.mesh = mesh()
            self.mesh.loadmodelfromfile(f"./engine3d/models/{file}")
            self.mesh.ambientColor = vec3d(255, 255, 255)

    def draw():
        pass

    def update():
        pass


class Camera(SceneObject):
    def __init__(self, x, y, z) -> None:
        super().__init__(x, y, z)
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
    def __init__(self, x, y, z, file=None) -> None:
        super().__init__(x, y, z, file)

        self.Camera = Camera(x, y, z)
        self.Camera2 = Camera(-74, -102, -86)
