### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Contact for more information about the Addon:
# Email:    germano.costa@ig.com.br
# Twitter:  wii_mano @mano_wii

bl_info = {
    "name": "Push Pull Face",
    "author": "Germano Cavalcante",
    "version": (0, 7),
    "blender": (2, 75, 0),
    "location": "View3D > TOOLS > Tools > Mesh Tools > Add: > Extrude Menu (Alt + E)",
    "description": "Push and pull face entities to sculpt 3d models",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?376618-Addon-Push-Pull-Face",
    "category": "Mesh"}

import bpy, bmesh
from bpy.types import Operator, Macro
#from mathutils import Vector
from bpy.props import FloatProperty

class Storage:
    mesh = bpy.context.object.data
    bm = bmesh.from_edit_mesh(mesh)
    auto_merge = False

class IntersectEdges(Operator):
    """Push and pull face entities to sculpt 3d models"""
    bl_idname = "mesh.intersect_edges"
    bl_label = "Intersect Edges"
    bl_options = {'REGISTER', 'GRAB_CURSOR', 'BLOCKING'}

    @classmethod
    def poll(cls, context):
        return  context.mode is not 'EDIT_MESH'
    
    def edges_BVH_overlap(self, edges1, edges2, precision = 0.0001):
        aco = [(v1.co,v2.co) for v1,v2 in [e.verts for e in edges1]]
        bco = [(v1.co,v2.co) for v1,v2 in [e.verts for e in edges2]]
        tmp_set1 = set()
        tmp_set2 = set()
        for i1, ed1 in enumerate(aco):
            for i2, ed2 in enumerate(bco):
                if ed1 != ed2:
                    a1, a2 = ed1
                    b1, b2 = ed2

                    a1x, a2x = a1.x, a2.x
                    b1x, b2x = b1.x, b2.x
                    bbx1 = (a1x, a2x) if a1x < a2x else (a2x, a1x)
                    bbx2 = (b1x, b2x) if b1x < b2x else (b2x, b1x)
                    if (bbx1[0] - precision) <= bbx2[1] and bbx1[1] >= (bbx2[0] - precision):
                        a1y, a2y = a1.y, a2.y
                        b1y, b2y = b1.y, b2.y
                        bby1 = (a1y, a2y) if a1y < a2y else (a2y, a1y)
                        bby2 = (b1y, b2y) if b1y < b2y else (b2y, b1y)
                        if (bby1[0] - precision) <= bby2[1] and bby1[1] >= (bby2[0] - precision):
                            a1z, a2z = a1.z, a2.z
                            b1z, b2z = b1.z, b2.z
                            bbz1 = (a1z, a2z) if a1z < a2z else (a2z, a1z)
                            bbz2 = (b1z, b2z) if b1z < b2z else (b2z, b1z)
                            if (bbz1[0] - precision) <= bbz2[1] and bbz1[1] >= (bbz2[0] - precision):
                                tmp_set1.add(edges1[i1])
                                tmp_set2.add(edges2[i2])

        return tmp_set1, tmp_set2

    def intersect_edges_edges(self, edges1, edges2, ignore = {}, precision = 4):
        fprec = .1**precision
        new_edges1 = set()
        new_edges2 = set()
        targetmap = {}
        exclude = {}
        for ed1 in edges1:
            for ed2 in edges2:
                if ed1 != ed2 and (ed1 not in ignore or ed2 not in ignore[ed1]):
                    a1 = ed1.verts[0]
                    a2 = ed1.verts[1]
                    b1 = ed2.verts[0]
                    b2 = ed2.verts[1]
                    
                    if a1 in {b1, b2} or a2 in {b1, b2}:
                        continue

                    v1 = a2.co-a1.co
                    v2 = b2.co-b1.co
                    v3 = a1.co-b1.co
                    
                    cross1 = v3.cross(v1)
                    cross2 = v3.cross(v2)
                    lc1 = cross1.x+cross1.y+cross1.z
                    lc2 = cross2.x+cross2.y+cross2.z
                    
                    if lc1 != 0 and lc2 != 0:
                        coplanar = (cross1/lc1).cross(cross2/lc2).to_tuple(2) == (0,0,0) #cross cross is very inaccurate
                    else:
                        coplanar = (cross1).cross(cross2).to_tuple(2) == (0,0,0)
                    
                    if coplanar: 
                        cross3 = v2.cross(v1)
                        lc3 = cross3.x+cross3.y+cross3.z

                        if abs(lc3) > fprec:                        
                            fac1 = lc2/lc3
                            fac2 = lc1/lc3
                            if 0 <= fac1 <= 1 and 0 <= fac2 <= 1:
                                rfac1 = round(fac1, precision)
                                rfac2 = round(fac2, precision)
                                set_ign = {ed2}

                                if 0 < rfac2 < 1:
                                    ne2, nv2 = bmesh.utils.edge_split(ed2, b1, fac2)
                                    new_edges2.update({ed2, ne2})
                                    set_ign.add(ne2)
                                elif rfac2 == 0:
                                    nv2 = b1
                                else:
                                    nv2 = b2

                                if 0 < rfac1 < 1:
                                    ne1, nv1 = bmesh.utils.edge_split(ed1, a1, fac1)
                                    new_edges1.update({ed1, ne1})
                                    exclude[ed1] = exclude[ne1] = set_ign
                                elif rfac1 == 0:
                                    nv1 = a1
                                    exclude[ed1] = set_ign
                                else:
                                    nv1 = a2
                                    exclude[ed1] = set_ign

                                if nv1 != nv2:
                                    targetmap[nv1] = nv2
                            #else:                            
                                #print('not intersect')
                        #else:
                            #print('colinear')
                    #else:
                        #print('not coplanar')
        if new_edges1 or new_edges2:
            edges1.update(new_edges1)
            edges2.update(new_edges2)
            ned, tar = self.intersect_edges_edges(edges1, edges2, ignore = exclude, precision = precision)
            if tar != targetmap:
                new_edges1.update(ned["new_edges1"])
                new_edges2.update(ned["new_edges2"])
                targetmap.update(tar)
            return {"new_edges1": new_edges1,
                    "new_edges2": new_edges2
                    }, targetmap
        else:
            return {"new_edges1": new_edges1,
                    "new_edges2": new_edges2
                    }, targetmap

    def execute(self, context):
        bm = Storage.bm
        sface = bm.faces.active
        if not sface:
            try:
                sface = [f for f in bm.faces if f.select][0]
            except:
                print('no active face')
                return {'FINISHED'}

        #### Using new module BVHTree to get overlap ####
        from mathutils.bvhtree import BVHTree
        # bvh_full
        bvh_full = BVHTree.FromBMesh(bm)

        # bvh_partial
        linked_faces = [[f for f in edge.link_faces if f != sface][0] for edge in sface.edges]
        linked_faces.append(sface)
        verts = []
        [[verts.append(v) for v in f.verts if v not in verts] for f in linked_faces]
        polygons = [[verts.index(v) for v in f.verts] for f in linked_faces]
        verts = [v.co for v in verts]
        bvh_partial = BVHTree.FromPolygons(verts, polygons, epsilon=0.0)
        
        # overlap
        overlap = bvh_partial.overlap(bvh_full)
        print(overlap)
        #### Ending the use of the new module BVHTree ####

        # edges to intersect
        edges = set()
        [[edges.add(ed) for ed in v.link_edges] for v in sface.verts]
        edges = list(edges)

        #edges to test intersect
        bm_edges = set()
        for _, f in overlap:
            for eds in bm.faces[f].edges:
                bm_edges.add(eds)
        bm_edges = list(bm_edges)

        # test bvh_intersect between edges to further reduce
        # TO_DO: returns relationship between edges that intersect
        set_edges, bm_edges = self.edges_BVH_overlap(edges, bm_edges, precision = 0.0001)

        # add vertices where intersect
        # TO_DO: use relationship between edges that intersect
        new_edges, targetmap = self.intersect_edges_edges(set_edges, bm_edges)

        # merge vertices
        if targetmap:
            bmesh.ops.weld_verts(bm, targetmap=targetmap)
            print('\'------------------------------------\'')
            print(new_edges)

        bmesh.update_edit_mesh(Storage.mesh, tessface=True, destructive=True)
        if Storage.auto_merge:
            context.scene.tool_settings.use_mesh_automerge = True
        return {'FINISHED'}

class ExtrudeDissolve(Operator):
    """Push and pull face entities to sculpt 3d models"""
    bl_idname = "mesh.extrude_dissolve"
    bl_label = "Extrude Dissolve"
    bl_options = {'REGISTER', 'GRAB_CURSOR', 'BLOCKING'}

    @classmethod
    def poll(cls, context):
        return  context.mode is not 'EDIT_MESH'

    def execute(self, context):
        Storage.auto_merge = context.scene.tool_settings.use_mesh_automerge
        if Storage.auto_merge:
            context.scene.tool_settings.use_mesh_automerge = False

        mesh = context.object.data
        bm = bmesh.from_edit_mesh(mesh)
        try:
            selection = bm.select_history[-1]
        except:
            for face in bm.faces:
                if face.select == True:
                    selection = face
                    break
            else:
                return {'FINISHED'}
        if not isinstance(selection, bmesh.types.BMFace):
            bpy.ops.mesh.extrude_region_move('INVOKE_DEFAULT')
            return {'FINISHED'}
        else:
            face = selection
            #face.select = False
            bpy.ops.mesh.select_all(action='DESELECT')
            geom = []
            for edge in face.edges:
                if abs(edge.calc_face_angle(0) - 1.5707963267948966) < 0.01: #self.angle_tolerance:
                    geom.append(edge)

            dict = bmesh.ops.extrude_discrete_faces(bm, faces = [face])
            
            for face in dict['faces']:
                bm.faces.active = face
                face.select = True
                sface = face
            dfaces = bmesh.ops.dissolve_edges(bm, edges = geom, use_verts=True, use_face_split=False)
            bmesh.update_edit_mesh(mesh, tessface=True, destructive=True)

        Storage.mesh = mesh
        Storage.bm = bm
        return {'FINISHED'}

class Push_Pull_Macro(Macro):
    """Overall macro for combining move and cursor operators"""
    bl_idname = "mesh.push_pull_face"
    bl_label = "Push/Pull Face Move"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

def operator_draw(self,context):
    layout = self.layout
    col = layout.column(align=True)
    col.operator("mesh.push_pull_face", text="Push/Pull Face")

def register():
    bpy.utils.register_class(Push_Pull_Macro)
    bpy.utils.register_class(ExtrudeDissolve)
    bpy.utils.register_class(IntersectEdges)
    
    Push_Pull_Macro.define("MESH_OT_extrude_dissolve")
    op = Push_Pull_Macro.define("TRANSFORM_OT_translate")
    op.properties.constraint_axis = (False, False, True)
    op.properties.constraint_orientation = 'NORMAL'
    op.properties.release_confirm = True
    Push_Pull_Macro.define("MESH_OT_intersect_edges")
    bpy.types.VIEW3D_MT_edit_mesh_extrude.append(operator_draw)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_extrude.remove(operator_draw)
    bpy.utils.register_class(Push_Pull_Macro)
    bpy.utils.register_class(ExtrudeDissolve)
    bpy.utils.register_class(IntersectEdges)

if __name__ == "__main__":
    register()
