from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Trek, Booking
from routes.decorators import role_required

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


def get_owned_trek_or_404(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != current_user.id:
        abort(403)
    return trek


@staff_bp.route('/dashboard')
@login_required
@role_required('staff')
def dashboard():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()

    trek_data = []
    for trek in assigned_treks:
        participant_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek_data.append({'trek': trek, 'participant_count': participant_count})

    return render_template('staff/dashboard.html', trek_data=trek_data)


@staff_bp.route('/treks/<int:trek_id>/update', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def update_trek(trek_id):
    trek = get_owned_trek_or_404(trek_id)

    if request.method == 'POST':
        new_total = int(request.form.get('total_slots'))
        already_booked = trek.total_slots - trek.available_slots
        trek.total_slots = new_total
        trek.available_slots = max(new_total - already_booked, 0)
        trek.status = request.form.get('status')

        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect(url_for('staff.dashboard'))

    return render_template('staff/update_trek.html', trek=trek)


@staff_bp.route('/treks/<int:trek_id>/participants')
@login_required
@role_required('staff')
def view_participants(trek_id):
    trek = get_owned_trek_or_404(trek_id)
    bookings = Booking.query.filter_by(trek_id=trek.id).all()
    return render_template('staff/participants.html', trek=trek, bookings=bookings)