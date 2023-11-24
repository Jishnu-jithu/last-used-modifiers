# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Last used Modifiers",
    "author": "Jishnu jithu",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "category": "Modifiers",
    "location": "Properties > Modifiers",
    "description": "Adds last used modifiers to the modifier menu.",
    "tracker_url": "",
}


import bpy
import os
import json
from bpy.types import Panel, Menu, Operator

# Get the path of the addon installation directory
addon_directory = os.path.dirname(os.path.realpath(__file__))

# Set the JSON file path within the addon installation directory
json_path = os.path.join(addon_directory, "last_used_modifiers.json")

class ModifierButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
    bl_options = {'HIDE_HEADER'}


class ModifierAddMenu:
    MODIFIER_TYPES_TO_LABELS = {
        enum_it.identifier: enum_it.name
        for enum_it in bpy.types.Modifier.bl_rna.properties["type"].enum_items_static
    }
    MODIFIER_TYPES_TO_ICONS = {
        enum_it.identifier: enum_it.icon
        for enum_it in bpy.types.Modifier.bl_rna.properties["type"].enum_items_static
    }
    MODIFIER_TYPES_I18N_CONTEXT = bpy.types.Modifier.bl_rna.properties["type"].translation_context

    @classmethod
    def operator_modifier_add(cls, layout, mod_type):
        layout.operator(
            "object.modifier_add",
            text=cls.MODIFIER_TYPES_TO_LABELS[mod_type],
            # Although these are operators, the label actually comes from an (enum) property,
            # so the property's translation context must be used here.
            text_ctxt=cls.MODIFIER_TYPES_I18N_CONTEXT,
            icon=cls.MODIFIER_TYPES_TO_ICONS[mod_type],
        ).type = mod_type


class DATA_PT_modifiers(ModifierButtonsPanel, Panel):
    bl_label = "Modifiers"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type != 'GPENCIL'

    def draw(self, context):
        layout = self.layout
        
        if context.scene.modifier.button_type == 'ADD_MODIFIER':
            layout.operator("wm.call_menu", text="Add Modifier", icon='ADD').name = "OBJECT_MT_modifier_add"
            
        elif context.scene.modifier.button_type == 'OLD_MENU':
            layout.menu("OBJECT_MT_old_menu", text="Add Modifier")
            
        elif context.scene.modifier.button_type == 'ALL':
            layout.operator("wm.call_menu", text="Add Modifier", icon='ADD').name = "OBJECT_MT_modifier_add"
            layout.separator()
            layout.menu("OBJECT_MT_old_menu", text="Add Modifier")
            
        layout.template_modifiers()
            
class Modifier_PG_Properties(bpy.types.PropertyGroup):
    button_type: bpy.props.EnumProperty(
        name="Button Type",
        description="Choose the type of button to display",
        items=[
            ('ADD_MODIFIER', "New", "Display the New Modifier button"),
            ('OLD_MENU', "Old", "Display the Old Modifier button"),
            ('ALL', "Both", "Display both buttons")
        ]
    )

class OBJECT_MT_modifier_add(ModifierAddMenu, Menu):
    bl_label = "Add Modifier"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        geometry_nodes_supported = ob_type in {'MESH', 'CURVE', 'CURVES', 'FONT', 'VOLUME', 'POINTCLOUD'}

        if layout.operator_context == 'EXEC_REGION_WIN':
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("WM_OT_search_single_menu", text="Search...",
                            icon='VIEWZOOM').menu_idname = "OBJECT_MT_modifier_add"
            layout.separator()
        
        
        layout.operator_context = 'EXEC_REGION_WIN'

        if geometry_nodes_supported:
            self.operator_modifier_add(layout, 'NODES')
            layout.separator()
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.menu("OBJECT_MT_modifier_add_edit")
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'VOLUME'}:
            layout.menu("OBJECT_MT_modifier_add_generate")
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE', 'VOLUME'}:
            layout.menu("OBJECT_MT_modifier_add_deform")
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.menu("OBJECT_MT_modifier_add_physics")

        if geometry_nodes_supported:
            layout.menu_contents("OBJECT_MT_modifier_add_root_catalogs")


class OBJECT_MT_modifier_add_edit(ModifierAddMenu, Menu):
    bl_label = "Edit"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type

        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Data Transfer", icon='MOD_DATA_TRANSFER').modifier = 'DATA_TRANSFER'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Mesh Cache", icon='MOD_MESHDEFORM').modifier = 'MESH_CACHE'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Mesh Sequence Cache", icon='MOD_MESHDEFORM').modifier = 'MESH_SEQUENCE_CACHE'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Normal Edit", icon='MOD_NORMALEDIT').modifier = 'NORMAL_EDIT'
            layout.operator('object.new_modifier_add', text="Weighted Normal", icon='MOD_NORMALEDIT').modifier = 'WEIGHTED_NORMAL'
            layout.operator('object.new_modifier_add', text="UV Project", icon='MOD_UVPROJECT').modifier = 'UV_PROJECT'
            layout.operator('object.new_modifier_add', text="UV Warp", icon='MOD_UVPROJECT').modifier = 'UV_WARP'
            layout.operator('object.new_modifier_add', text="Vertex Weight Edit", icon='MOD_VERTEX_WEIGHT').modifier = 'VERTEX_WEIGHT_EDIT'
            layout.operator('object.new_modifier_add', text="Vertex Weight Mix", icon='MOD_VERTEX_WEIGHT').modifier = 'VERTEX_WEIGHT_MIX'
            layout.operator('object.new_modifier_add', text="Vertex Weight Proximity", icon='MOD_VERTEX_WEIGHT').modifier = 'VERTEX_WEIGHT_PROXIMITY'

        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)



class OBJECT_MT_modifier_add_generate(ModifierAddMenu, Menu):
    bl_label = "Generate"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type

        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Array", icon='MOD_ARRAY').modifier = 'ARRAY'
            layout.operator('object.new_modifier_add', text="Bevel", icon='MOD_BEVEL').modifier = 'BEVEL'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Boolean", icon='MOD_BOOLEAN').modifier = 'BOOLEAN'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Build", icon='MOD_BUILD').modifier = 'BUILD'
            layout.operator('object.new_modifier_add', text="Decimate", icon='MOD_DECIM').modifier = 'DECIMATE'
            layout.operator('object.new_modifier_add', text="Edge Split", icon='MOD_EDGESPLIT').modifier = 'EDGE_SPLIT'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Mask", icon='MOD_MASK').modifier = 'MASK'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Mirror", icon='MOD_MIRROR').modifier = 'MIRROR'
        if ob_type == 'VOLUME':
            layout.operator('object.new_modifier_add', text="Mesh to Volume", icon='MOD_EXPLODE').modifier = 'MESH_TO_VOLUME'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Multires", icon='MOD_MULTIRES').modifier = 'MULTIRES'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Remesh", icon='MOD_REMESH').modifier = 'REMESH'
            layout.operator('object.new_modifier_add', text="Screw", icon='MOD_SCREW').modifier = 'SCREW'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Skin", icon='MOD_SKIN').modifier = 'SKIN'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Solidify", icon='MOD_SOLIDIFY').modifier = 'SOLIDIFY'
            layout.operator('object.new_modifier_add', text="Subdivision Surface", icon='MOD_SUBSURF').modifier = 'SUBSURF'
            layout.operator('object.new_modifier_add', text="Triangulate", icon='MOD_TRIANGULATE').modifier = 'TRIANGULATE'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Volume to Mesh", icon='MOD_CAST').modifier = 'VOLUME_TO_MESH'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Weld", icon='AUTOMERGE_OFF').modifier = 'WELD'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Wireframe", icon='MOD_WIREFRAME').modifier = 'WIREFRAME'
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)



class OBJECT_MT_modifier_add_deform(ModifierAddMenu, Menu):
    bl_label = "Deform"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type

        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Armature", icon='MOD_ARMATURE').modifier = 'ARMATURE'
            layout.operator('object.new_modifier_add', text="Cast", icon='MOD_CAST').modifier = 'CAST'
            layout.operator('object.new_modifier_add', text="Curve", icon='MOD_CURVE').modifier = 'CURVE'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Displace", icon='MOD_DISPLACE').modifier = 'DISPLACE'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Hook", icon='HOOK').modifier = 'HOOK'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Laplacian Deform", icon='MOD_MESHDEFORM').modifier = 'LAPLACIANDEFORM'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Lattice", icon='MOD_LATTICE').modifier = 'LATTICE'
            layout.operator('object.new_modifier_add', text="Mesh Deform", icon='MOD_MESHDEFORM').modifier = 'MESH_DEFORM'
            layout.operator('object.new_modifier_add', text="Shrinkwrap", icon='MOD_SHRINKWRAP').modifier = 'SHRINKWRAP'
            layout.operator('object.new_modifier_add', text="Simple Deform", icon='MOD_SIMPLEDEFORM').modifier = 'SIMPLE_DEFORM'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            layout.operator('object.new_modifier_add', text="Smooth", icon='MOD_SMOOTH').modifier = 'SMOOTH'
        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Corrective Smooth", icon='MOD_SMOOTH').modifier = 'CORRECTIVE_SMOOTH'
            layout.operator('object.new_modifier_add', text="Laplacian Smooth", icon='MOD_SMOOTH').modifier = 'LAPLACIANSMOOTH'
            layout.operator('object.new_modifier_add', text="Surface Deform", icon='MOD_MESHDEFORM').modifier = 'SURFACE_DEFORM'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Warp", icon='MOD_WARP').modifier = 'WARP'
            layout.operator('object.new_modifier_add', text="Wave", icon='MOD_WAVE').modifier = 'WAVE'
        if ob_type == 'VOLUME':
            layout.operator('object.new_modifier_add', text="Volume Displace", icon='MOD_EXPLODE').modifier = 'VOLUME_DISPLACE'
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_physics(ModifierAddMenu, Menu):
    bl_label = "Physics"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type

        if ob_type == 'MESH':
            layout.operator('object.new_modifier_add', text="Cloth", icon='MOD_CLOTH').modifier = 'CLOTH'
            layout.operator('object.new_modifier_add', text="Collision", icon='MOD_PHYSICS').modifier = 'COLLISION'
            layout.operator('object.new_modifier_add', text="Dynamic Paint", icon='MOD_DYNAMICPAINT').modifier = 'DYNAMIC_PAINT'
            layout.operator('object.new_modifier_add', text="Explode", icon='MOD_EXPLODE').modifier = 'EXPLODE'
            layout.operator('object.new_modifier_add', text="Fluid", icon='MOD_FLUID').modifier = 'FLUID'
            layout.operator('object.new_modifier_add', text="Ocean", icon='MOD_OCEAN').modifier = 'OCEAN'
            layout.operator('object.new_modifier_add', text="Particle Instance", icon='MOD_PARTICLE_INSTANCE').modifier = 'PARTICLE_INSTANCE'
            layout.operator('object.new_modifier_add', text="Particle System", icon='MOD_PARTICLES').modifier = 'PARTICLE_SYSTEM'

        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            layout.operator('object.new_modifier_add', text="Soft Body", icon='MOD_SOFT').modifier = 'SOFT_BODY'

        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)

class Old_modifier_menu(bpy.types.Menu):
    bl_label = "Old Modifier Menu"
    bl_idname = "OBJECT_MT_old_menu"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        split = layout.split()
        ob_type = context.object.type
        
        col = split.column()
        col.label(text="Modify")
        
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Data Transfer", icon='MOD_DATA_TRANSFER').modifier = 'DATA_TRANSFER'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Mesh Cache", icon='MOD_MESHDEFORM').modifier = 'MESH_CACHE'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Mesh Sequence Cache", icon='MOD_MESHDEFORM').modifier = 'MESH_SEQUENCE_CACHE'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Normal Edit", icon='MOD_NORMALEDIT').modifier = 'NORMAL_EDIT'
            col.operator('object.new_modifier_add', text="Weighted Normal", icon='MOD_NORMALEDIT').modifier = 'WEIGHTED_NORMAL'
            col.operator('object.new_modifier_add', text="UV Project", icon='MOD_UVPROJECT').modifier = 'UV_PROJECT'
            col.operator('object.new_modifier_add', text="UV Warp", icon='MOD_UVPROJECT').modifier = 'UV_WARP'
            col.operator('object.new_modifier_add', text="Vertex Weight Edit", icon='MOD_VERTEX_WEIGHT').modifier = 'VERTEX_WEIGHT_EDIT'
            col.operator('object.new_modifier_add', text="Vertex Weight Mix", icon='MOD_VERTEX_WEIGHT').modifier = 'VERTEX_WEIGHT_MIX'
            col.operator('object.new_modifier_add', text="Vertex Weight Proximity", icon='MOD_VERTEX_WEIGHT').modifier = 'VERTEX_WEIGHT_PROXIMITY'

        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)
        
        col = split.column()
        col.label(text="Generate")
        
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Array", icon='MOD_ARRAY').modifier = 'ARRAY'
            col.operator('object.new_modifier_add', text="Bevel", icon='MOD_BEVEL').modifier = 'BEVEL'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Boolean", icon='MOD_BOOLEAN').modifier = 'BOOLEAN'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Build", icon='MOD_BUILD').modifier = 'BUILD'
            col.operator('object.new_modifier_add', text="Decimate", icon='MOD_DECIM').modifier = 'DECIMATE'
            col.operator('object.new_modifier_add', text="Edge Split", icon='MOD_EDGESPLIT').modifier = 'EDGE_SPLIT'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Mask", icon='MOD_MASK').modifier = 'MASK'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Mirror", icon='MOD_MIRROR').modifier = 'MIRROR'
        if ob_type == 'VOLUME':
            col.operator('object.new_modifier_add', text="Mesh to Volume", icon='MOD_EXPLODE').modifier = 'MESH_TO_VOLUME'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Multiresolution", icon='MOD_MULTIRES').modifier = 'MULTIRES'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Remesh", icon='MOD_REMESH').modifier = 'REMESH'
            col.operator('object.new_modifier_add', text="Screw", icon='MOD_SCREW').modifier = 'SCREW'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Skin", icon='MOD_SKIN').modifier = 'SKIN'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Solidify", icon='MOD_SOLIDIFY').modifier = 'SOLIDIFY'
            col.operator('object.new_modifier_add', text="Subdivision Surface", icon='MOD_SUBSURF').modifier = 'SUBSURF'
            col.operator('object.new_modifier_add', text="Triangulate", icon='MOD_TRIANGULATE').modifier = 'TRIANGULATE'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Volume to Mesh", icon='MOD_CAST').modifier = 'VOLUME_TO_MESH'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Weld", icon='AUTOMERGE_OFF').modifier = 'WELD'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Wireframe", icon='MOD_WIREFRAME').modifier = 'WIREFRAME'
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)
        
        
        col = split.column()
        col.label(text="Deform")
        
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Armature", icon='MOD_ARMATURE').modifier = 'ARMATURE'
            col.operator('object.new_modifier_add', text="Cast", icon='MOD_CAST').modifier = 'CAST'
            col.operator('object.new_modifier_add', text="Curve", icon='MOD_CURVE').modifier = 'CURVE'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Displace", icon='MOD_DISPLACE').modifier = 'DISPLACE'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Hook", icon='HOOK').modifier = 'HOOK'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Laplacian Deform", icon='MOD_MESHDEFORM').modifier = 'LAPLACIANDEFORM'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Lattice", icon='MOD_LATTICE').modifier = 'LATTICE'
            col.operator('object.new_modifier_add', text="Mesh Deform", icon='MOD_MESHDEFORM').modifier = 'MESH_DEFORM'
            col.operator('object.new_modifier_add', text="Shrinkwrap", icon='MOD_SHRINKWRAP').modifier = 'SHRINKWRAP'
            col.operator('object.new_modifier_add', text="Simple Deform", icon='MOD_SIMPLEDEFORM').modifier = 'SIMPLE_DEFORM'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            col.operator('object.new_modifier_add', text="Smooth", icon='MOD_SMOOTH').modifier = 'SMOOTH'
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Corrective Smooth", icon='MOD_SMOOTH').modifier = 'CORRECTIVE_SMOOTH'
            col.operator('object.new_modifier_add', text="Laplacian Smooth", icon='MOD_SMOOTH').modifier = 'LAPLACIANSMOOTH'
            col.operator('object.new_modifier_add', text="Surface Deform", icon='MOD_MESHDEFORM').modifier = 'SURFACE_DEFORM'
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Warp", icon='MOD_WARP').modifier = 'WARP'
            col.operator('object.new_modifier_add', text="Wave", icon='MOD_WAVE').modifier = 'WAVE'
        if ob_type == 'VOLUME':
            col.operator('object.new_modifier_add', text="Volume Displace", icon='MOD_EXPLODE').modifier = 'VOLUME_DISPLACE'
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)
        
        
        col = split.column()
        col.label(text="Physics")
        
        if ob_type == 'MESH':
            col.operator('object.new_modifier_add', text="Cloth", icon='MOD_CLOTH').modifier = 'CLOTH'
            col.operator('object.new_modifier_add', text="Collision", icon='MOD_PHYSICS').modifier = 'COLLISION'
            col.operator('object.new_modifier_add', text="Dynamic Paint", icon='MOD_DYNAMICPAINT').modifier = 'DYNAMIC_PAINT'
            col.operator('object.new_modifier_add', text="Explode", icon='MOD_EXPLODE').modifier = 'EXPLODE'
            col.operator('object.new_modifier_add', text="Fluid", icon='MOD_FLUID').modifier = 'FLUID'
            col.operator('object.new_modifier_add', text="Ocean", icon='MOD_OCEAN').modifier = 'OCEAN'
            col.operator('object.new_modifier_add', text="Particle Instance", icon='MOD_PARTICLE_INSTANCE').modifier = 'PARTICLE_INSTANCE'
            col.operator('object.new_modifier_add', text="Particle System", icon='MOD_PARTICLES').modifier = 'PARTICLE_SYSTEM'

        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            col.operator('object.new_modifier_add', text="Soft Body", icon='MOD_SOFT').modifier = 'SOFT_BODY'

        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


modifier_icons = {
    'DATA_TRANSFER': 'MOD_DATA_TRANSFER',
    'MESH_CACHE': 'MOD_MESHDEFORM',
    'MESH_SEQUENCE_CACHE': 'MOD_MESHDEFORM',
    'NORMAL_EDIT': 'MOD_NORMALEDIT',
    'WEIGHTED_NORMAL': 'MOD_NORMALEDIT',
    'UV_PROJECT': 'MOD_UVPROJECT',
    'UV_WARP': 'MOD_UVPROJECT',
    'VERTEX_WEIGHT_EDIT': 'MOD_VERTEX_WEIGHT',
    'VERTEX_WEIGHT_MIX': 'MOD_VERTEX_WEIGHT',
    'VERTEX_WEIGHT_PROXIMITY': 'MOD_VERTEX_WEIGHT',
    'ARRAY': 'MOD_ARRAY',
    'BEVEL': 'MOD_BEVEL',
    'BOOLEAN': 'MOD_BOOLEAN',
    'BUILD': 'MOD_BUILD',
    'DECIMATE': 'MOD_DECIM',
    'EDGE_SPLIT': 'MOD_EDGESPLIT',
    'MASK': 'MOD_MASK',
    'MIRROR': 'MOD_MIRROR',
    'MESH_TO_VOLUME': 'MOD_EXPLODE',
    'MULTIRES': 'MOD_MULTIRES',
    'REMESH': 'MOD_REMESH',
    'SCREW': 'MOD_SCREW',
    'SKIN': 'MOD_SKIN',
    'SOLIDIFY': 'MOD_SOLIDIFY',
    'SUBSURF': 'MOD_SUBSURF',
    'TRIANGULATE': 'MOD_TRIANGULATE',
    'VOLUME_TO_MESH': 'MOD_CAST',
    'WELD': 'AUTOMERGE_OFF',
    'WIREFRAME': 'MOD_WIREFRAME',
    'ARMATURE': 'MOD_ARMATURE',
    'CAST': 'MOD_CAST',
    'CURVE': 'MOD_CURVE',
    'DISPLACE': 'MOD_DISPLACE',
    'HOOK': 'HOOK',
    'LAPLACIANDEFORM': 'MOD_MESHDEFORM',
    'LATTICE': 'MOD_LATTICE',
    'MESH_DEFORM': 'MOD_MESHDEFORM',
    'SHRINKWRAP': 'MOD_SHRINKWRAP',
    'SIMPLE_DEFORM': 'MOD_SIMPLEDEFORM',
    'SMOOTH': 'MOD_SMOOTH',
    'CORRECTIVE_SMOOTH': 'MOD_SMOOTH',
    'LAPLACIANSMOOTH': 'MOD_SMOOTH',
    'SURFACE_DEFORM': 'MOD_MESHDEFORM',
    'WARP': 'MOD_WARP',
    'WAVE': 'MOD_WAVE',
    'VOLUME_DISPLACE': 'MOD_EXPLODE',
    'CLOTH': 'MOD_CLOTH',
    'COLLISION': 'MOD_PHYSICS',
    'DYNAMIC_PAINT': 'MOD_DYNAMICPAINT',
    'EXPLODE': 'MOD_EXPLODE',
    'FLUID': 'MOD_FLUID',
    'OCEAN': 'MOD_OCEAN',
    'PARTICLE_INSTANCE': 'MOD_PARTICLE_INSTANCE',
    'PARTICLE_SYSTEM': 'MOD_PARTICLES',
    'SOFT_BODY': 'MOD_SOFT',
}


def save_last_used_modifiers():
    # Save the last used modifiers to a JSON file
    with open(json_path, "w") as f:
        json.dump(last_used_modifiers, f)

def load_last_used_modifiers():
    # Load the last used modifiers from a JSON file
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    else:
        return []

class Modifiers_OT_Add(bpy.types.Operator):
    bl_idname = "object.new_modifier_add"
    bl_label = "Add Modifier (Custom)"

    modifier: bpy.props.StringProperty()

    def execute(self, context):
        global last_used_modifiers

        # Call the original modifier_add operator
        bpy.ops.object.modifier_add(type=self.modifier)

        # Update the list of last used modifiers
        if self.modifier in last_used_modifiers:
            # Move the modifier to the end of the list
            last_used_modifiers.remove(self.modifier)
        last_used_modifiers.append(self.modifier)

        # Keep only the last custom_modifier_count modifiers
        last_used_modifiers = last_used_modifiers[-context.scene.custom_modifier_count:]

        # Save the updated list to a JSON file
        save_last_used_modifiers()

        return {'FINISHED'}

def draw_func(self, context):
    layout = self.layout
    
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(addon_directory, "last_used_modifiers.json")

    if os.path.exists(json_path) and not bpy.context.scene.custom_modifier_count == 0:
        layout.separator()

        # Draw the last used modifiers in reverse order with icons
        for modifier in reversed(last_used_modifiers):
            if modifier in modifier_icons:
                icon = modifier_icons[modifier]
            else:
                icon = 'MODIFIER'  # Default icon if not found in the mapping
            
            op = layout.operator(Modifiers_OT_Add.bl_idname, text=modifier.capitalize(), icon=icon)
            op.modifier = modifier

def draw_func_style(self, context):
    layout = self.layout
    
    if bpy.context.space_data.context == 'MODIFIER':

        layout.separator()
        layout.prop(context.scene.modifier, "button_type", text="Button Type", expand=True)
        
        if not context.scene.modifier.button_type == 'OLD_MENU':
            layout.separator()
            layout.prop(context.scene, "custom_modifier_count", text="Last Used Modifiers")

# Initialize the list of last used modifiers
last_used_modifiers = load_last_used_modifiers()

classes = (
    DATA_PT_modifiers,
    OBJECT_MT_modifier_add,
    OBJECT_MT_modifier_add_edit,
    OBJECT_MT_modifier_add_generate,
    OBJECT_MT_modifier_add_deform,
    OBJECT_MT_modifier_add_physics,
    Modifiers_OT_Add,
    Old_modifier_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.custom_modifier_count = bpy.props.IntProperty(
        name="Last Used Modifier Count",
        default=4,
        min=0,
        max=6,
    )
    
    bpy.types.PROPERTIES_PT_options.append(draw_func_style)
    bpy.types.OBJECT_MT_modifier_add.append(draw_func)
    
    try:
        bpy.utils.register_class(Modifier_PG_Properties)
        bpy.types.Scene.modifier = bpy.props.PointerProperty(type=Modifier_PG_Properties)
    except ValueError:
        pass
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # Reload scripts to restore the original modifier panel
    bpy.ops.script.reload()
    
    # Remove functions
    try:
        bpy.types.PROPERTIES_PT_options.remove(draw_func_style)
    except ValueError:
        pass
    
if __name__ == "__main__":
    register()