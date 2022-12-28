# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "blender-lithophane",
    "author": "Ingvar Out",
    "description": "Create a lithophane from image",
    "blender": (3, 5, 0),
    "version": (0, 1, 0),
    "location": "3D Viewport",
    "warning": "",
    "category": "Add Mesh"
}

import pathlib
import bpy

ASSETS_PATH = pathlib.Path(__file__).parent.absolute() / "lithophane.blend"


def load_assets():
    """Link the CPVT assets blend file."""
    if not load_assets.loaded:
        with bpy.data.libraries.load(
            filepath=str(ASSETS_PATH),
                link=True, assets_only=True) as (data_from, data_to):
            for node_group in data_from.node_groups:
                data_to.node_groups.append(node_group)
        load_assets.loaded = True


load_assets.loaded = False


class CreateLithophane(bpy.types.Operator):
    """Turn an image into a lithophane."""

    bl_idname = "object.create_lithophane"
    bl_label = "Create Lithophane"

    def execute(self, context):
        """Turn selected image into specified lithophane type."""

        # Create and add lithophane geometry node
        load_assets()
        node_group = bpy.data.node_groups.new(
            type="GeometryNodeTree", name="gm_lithophane"
        )
        image_node = node_group.nodes.new(
            type='GeometryNodeInputImage')
        try:
            image_node.image = bpy.data.images.load(
                context.scene.blit_image_path)
        except RuntimeError:
            self.report({'ERROR'}, 'Image loading failed')
            return {'CANCELLED'}

        lithophane_node_group_copy = (
            bpy.data.node_groups[f'Lithophane {context.scene.blit_type} v2'].copy())
        litho_ng = node_group.nodes.new(type="GeometryNodeGroup")
        litho_ng.name = 'Lithophane'
        litho_ng.node_tree = lithophane_node_group_copy
        links = node_group.links
        links.new(image_node.outputs['Image'], litho_ng.inputs['Image'])
        litho_ng.location[0] += 290

        output_node = node_group.nodes.new(type="NodeGroupOutput")
        output_node.location = (480, 0)
        links.new(litho_ng.outputs['Geometry'], output_node.inputs[0])

        # add object 
        mesh = bpy.data.meshes.new("lithophane")
        obj = bpy.data.objects.new(
            name=f"lithophane {context.scene.blit_type}", object_data=mesh)
        obj.blit_is_lithophane = True
        context.scene.collection.objects.link(obj)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        geom_node = obj.modifiers.new(type='NODES', name='lithophane')
        geom_node.node_group = node_group

        self.report({'INFO'}, 'Lithophane added')
        return {'FINISHED'}


class LithophanePanel(bpy.types.Panel):
    """Lithophane UI in viewport side panel."""

    bl_idname = 'BLITHOPHANE_PT_Lithophane'
    bl_label = 'Lithophane'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "lithophane"

    def draw(self, context):
        """Define UI layout."""
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, 'blit_image_path')
        row = layout.row()
        row.prop(context.scene, 'blit_type')

        row = layout.row()
        row.scale_y = 1.4
        row.operator('object.create_lithophane')

        box = layout.box()
        row = box.row()
        if context.selected_objects and context.object.blit_is_lithophane:
            row.label(text=f"Selection: '{context.object.name}'")

            node_group = context.object.modifiers['lithophane'].node_group
            for input_ in node_group.nodes['Lithophane'].inputs:
                if input_.name != 'Image':
                    row = box.row()
                    row.prop(input_, 'default_value', text=input_.name)
        else:
            row.label(text='Selection: None')


def register():
    """Add classes and types to Blender."""
    bpy.types.Object.blit_is_lithophane = bpy.props.BoolProperty()
    bpy.types.Scene.blit_image_path = bpy.props.StringProperty(
        name='Image Path', subtype='FILE_PATH')
    bpy.types.Scene.blit_type = bpy.props.EnumProperty(
        name='Geometry Type',
        items = [
            tuple(['Plane'] * 3),
            tuple(['Arc'] * 3),
            tuple(['Cylinder'] * 3),
        ]
    )
    bpy.utils.register_class(CreateLithophane)
    bpy.utils.register_class(LithophanePanel)


def unregister():
    """Remove classes and types from Blender."""
    del bpy.types.Object.blit_is_lithophane
    del bpy.types.Scene.blit_image_path
    del bpy.types.Scene.blit_type
    bpy.utils.unregister_class(CreateLithophane)
    bpy.utils.unregister_class(LithophanePanel)
