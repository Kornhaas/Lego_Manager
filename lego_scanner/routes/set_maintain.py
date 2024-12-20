from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from models import db, UserSet, Part, Minifigure, UserMinifigurePart
from services.lookup_service import load_master_lookup
from sqlalchemy.orm import joinedload
import os

set_maintain_bp = Blueprint('set_maintain', __name__)

@set_maintain_bp.route('/set_maintain', methods=['GET'])
def set_maintain():
    """
    Displays the list of user sets.
    """
    user_sets = UserSet.query.options(
        joinedload(UserSet.template_set),
        joinedload(UserSet.parts),
        joinedload(UserSet.minifigures)
    ).order_by(UserSet.id.desc()).all()

    # Add completeness percentage to each user set
    sets_with_completeness = []
    for user_set in user_sets:
        total_quantity = 0
        total_have_quantity = 0

        # Calculate parts completeness
        for part in user_set.parts:
            total_quantity += part.quantity
            total_have_quantity += part.have_quantity

        # Exclude minifigures from the completeness calculation

        # Calculate user minifigure parts completeness
        user_minifigure_parts = UserMinifigurePart.query.filter_by(user_set_id=user_set.id).all()
        for part in user_minifigure_parts:
            total_quantity += part.quantity
            total_have_quantity += part.have_quantity

        # Compute completeness percentage
        completeness_percentage = 0
        if total_quantity > 0:
            completeness_percentage = (total_have_quantity / total_quantity) * 100

        sets_with_completeness.append({
            'user_set': user_set,
            'completeness_percentage': round(completeness_percentage, 2)
        })

    return render_template('set_maintain.html', sets_with_completeness=sets_with_completeness)


@set_maintain_bp.route('/set_maintain/<int:user_set_id>', methods=['GET'])
def get_user_set_details(user_set_id):
    """
    Returns the details of a specific UserSet, including its parts, minifigures, and user minifigure parts.
    """
    master_lookup = load_master_lookup()
    user_set = UserSet.query.options(
        joinedload(UserSet.parts),
        joinedload(UserSet.minifigures)
    ).get_or_404(user_set_id)

    # Fetch user_minifigure_parts based on user_set_id
    user_minifigure_parts = UserMinifigurePart.query.filter_by(user_set_id=user_set_id).all()

    # Calculate completeness
    total_quantity = 0
    total_have_quantity = 0

    for part in user_set.parts:
        if not part.is_spare:  # Exclude spare parts
            total_quantity += part.quantity
            total_have_quantity += part.have_quantity

    # Exclude minifigures from the completeness calculation

    for part in user_minifigure_parts:
        total_quantity += part.quantity
        total_have_quantity += part.have_quantity

    completeness_percentage = 0
    if total_quantity > 0:
        completeness_percentage = (total_have_quantity / total_quantity) * 100

    # Helper function for location and status
    def enrich_item(item, master_lookup):
        part_data = master_lookup.get(item.part_num, {})
        return {
            'id': item.id,
            'part_num': item.part_num,
            'name': item.name,
            'quantity': item.quantity,
            'is_spare': item.is_spare,
            'have_quantity': item.have_quantity,
            'color': item.color,  # Add color
            'part_img_url': item.part_img_url,
            'location': f"Location: {part_data.get('location', 'Unknown')}, "
                        f"Level: {part_data.get('level', 'Unknown')}, "
                        f"Box: {part_data.get('box', 'Unknown')}" if part_data else "Not Specified",
            'status': "Available" if part_data else "Not Available"
        }

    parts = [enrich_item(part, master_lookup) for part in user_set.parts]
    minifigs = [
        {
            'id': minifig.id,
            'fig_num': minifig.fig_num,
            'name': minifig.name,
            'quantity': minifig.quantity,
            'have_quantity': minifig.have_quantity,
            'img_url': minifig.img_url,
            'location': f"Location: {master_lookup.get(minifig.fig_num, {}).get('location', 'Unknown')}, "
                        f"Level: {master_lookup.get(minifig.fig_num, {}).get('level', 'Unknown')}, "
                        f"Box: {master_lookup.get(minifig.fig_num, {}).get('box', 'Unknown')}" if master_lookup.get(minifig.fig_num) else "Not Specified",
            'status': "Available" if master_lookup.get(minifig.fig_num) else "Not Available"
        }
        for minifig in user_set.minifigures
    ]
    minifigure_parts = [enrich_item(part, master_lookup) for part in user_minifigure_parts]

    return jsonify({
        'set_img_url': user_set.template_set.set_img_url,
        'parts': parts,
        'minifigs': minifigs,
        'minifigure_parts': minifigure_parts,
        'status': user_set.status,
        'completeness_percentage': round(completeness_percentage, 2)
    })

@set_maintain_bp.route('/set_maintain/update', methods=['POST'])
def update_user_set():
    """
    Updates the parts, minifigures, and user minifigure parts owned for a specific UserSet.
    """
    user_set_id = request.form.get('user_set_id')
    status = request.form.get('status')
    user_set = UserSet.query.get_or_404(user_set_id)

    try:
        # Update parts
        for part in user_set.parts:
            have_quantity = request.form.get(f'part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        # Update minifigures
        for minifig in user_set.minifigures:
            have_quantity = request.form.get(f'minifig_id_{minifig.id}')
            if have_quantity is not None:
                minifig.have_quantity = max(0, min(minifig.quantity, int(have_quantity)))
                db.session.add(minifig)

        # Update user minifigure parts
        user_minifigure_parts = UserMinifigurePart.query.filter_by(user_set_id=user_set_id).all()
        for part in user_minifigure_parts:
            have_quantity = request.form.get(f'minifig_part_id_{part.id}')
            if have_quantity is not None:
                part.have_quantity = max(0, min(part.quantity, int(have_quantity)))
                db.session.add(part)

        # Update status
        if status:
            user_set.status = status
            db.session.add(user_set)

        db.session.commit()
        flash(f"User Set for {user_set.template_set.set_number} updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating UserSet: {e}")
        flash("Failed to update UserSet.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))

@set_maintain_bp.route('/set_maintain/delete/<int:user_set_id>', methods=['POST'])
def delete_user_set(user_set_id):
    """
    Deletes a specific UserSet from the database.
    """
    try:
        # Query the UserSet instance with its related template_set to avoid lazy loading issues
        user_set = UserSet.query.options(joinedload(UserSet.template_set)).get_or_404(user_set_id)

        # Log the template set number for confirmation
        template_set_number = user_set.template_set.set_number
        db.session.delete(user_set)
        db.session.commit()

        flash(f"User Set for {template_set_number} deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting UserSet: {e}")
        flash("Failed to delete User Set.", "danger")

    return redirect(url_for('set_maintain.set_maintain'))


@set_maintain_bp.route('/set_maintain/generate_label', methods=['POST'])
def generate_label():
    """
    Generate a DrawIO file for a LEGO set label and provide it for download.
    """
    set_id = request.json.get('set_id')
    box_size = request.json.get('box_size')
    current_app.logger.info(f"Generating label for set {set_id} with box size {box_size}")
    try:
        #lego_set = UserSet.query.join(UserSet.template_set).filter(UserSet.id == set_id).first()
        lego_set = UserSet.query.join(UserSet.template_set).filter(UserSet.id == set_id).first()
        if not lego_set:
            return jsonify({'error': 'Set not found in the database'}), 404

        lego_data = {
            "set_num": lego_set.template_set.set_number,
            "name": lego_set.template_set.name,
            "set_img_url": lego_set.template_set.set_img_url,
            "box_id": str(lego_set.id)#"box_id": str(lego_set.template_set.id)

        }

        drawio_template = f"templates/{box_size}.drawio"
        if not os.path.exists(drawio_template):
            return jsonify({'error': f'DrawIO template {box_size} not found'}), 400

        replacements = {
            "BOX_LONG_TITLE": f"LEGO SET - {lego_data['set_num']} - {lego_data['name'].replace('&', 'and')}",
            "BOX_SHORT_TITLE": lego_data['set_num'],
            "IMAGE_CONTEXT": lego_data['set_img_url'],
            "BOX_ID": lego_data['box_id'],
        }

        with open(drawio_template, 'r', encoding='utf-8') as file:
            content = file.read()
            for key, value in replacements.items():
                content = content.replace(key, value)

        output_file = f"output/{set_id}_{box_size}.drawio"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)

        return send_file(output_file, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error generating label: {e}")
        return jsonify({'error': 'Failed to generate label'}), 500