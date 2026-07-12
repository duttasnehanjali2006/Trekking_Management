from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Trek, User, Booking
from routes.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def validate_trek_dates(start_date, end_date, duration):
    if end_date < start_date:
        return 'End date cannot be before the start date.'

    expected_duration = (end_date - start_date).days + 1
    if duration != expected_duration:
        return (
            f'Duration ({duration} days) does not match the selected dates '
            f'(start to end date spans {expected_duration} days). '
            f'Please correct the duration or the dates.'
        )

    return None


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
    )


@admin_bp.route('/treks')
@login_required
@role_required('admin')
def manage_treks():
    search_query = request.args.get('q', '').strip()

    treks_query = Trek.query
    if search_query:
        if search_query.isdigit():
            treks_query = treks_query.filter(Trek.id == int(search_query))
        else:
            treks_query = treks_query.filter(Trek.name.ilike(f'%{search_query}%'))

    all_treks = treks_query.all()
    return render_template('admin/manage_treks.html', treks=all_treks, search_query=search_query)


@admin_bp.route('/treks/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_trek():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        duration = int(request.form.get('duration'))
        total_slots = int(request.form.get('total_slots'))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        error = validate_trek_dates(start_date, end_date, duration)
        if error:
            flash(error, 'danger')
            return render_template('admin/trek_form.html', trek=None)

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            total_slots=total_slots,
            available_slots=total_slots,
            start_date=start_date,
            end_date=end_date,
            status='Pending',
        )

        db.session.add(new_trek)
        db.session.commit()

        flash('Trek created successfully.', 'success')
        return redirect(url_for('admin.manage_treks'))

    return render_template('admin/trek_form.html', trek=None)


@admin_bp.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':
        trek.name = request.form.get('name')
        trek.location = request.form.get('location')
        trek.difficulty = request.form.get('difficulty')
        new_duration = int(request.form.get('duration'))
        new_start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        new_end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        error = validate_trek_dates(new_start_date, new_end_date, new_duration)
        if error:
            flash(error, 'danger')
            return render_template('admin/trek_form.html', trek=trek)

        trek.duration = new_duration
        trek.start_date = new_start_date
        trek.end_date = new_end_date
        trek.status = request.form.get('status')

        new_total = int(request.form.get('total_slots'))
        already_booked = trek.total_slots - trek.available_slots
        trek.total_slots = new_total
        trek.available_slots = max(new_total - already_booked, 0)

        db.session.commit()

        flash('Trek updated successfully.', 'success')
        return redirect(url_for('admin.manage_treks'))

    return render_template('admin/trek_form.html', trek=trek)


@admin_bp.route('/treks/<int:trek_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    meaningful_bookings = Booking.query.filter(
        Booking.trek_id == trek.id,
        Booking.status.in_(['Booked', 'Completed']),
    ).count()

    if meaningful_bookings > 0:
        flash('This trek cannot be deleted because it has active or completed bookings. Set its status to Closed instead.', 'danger')
        return redirect(url_for('admin.manage_treks'))

    Booking.query.filter_by(trek_id=trek.id).delete()

    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted.', 'info')
    return redirect(url_for('admin.manage_treks'))


@admin_bp.route('/treks/<int:trek_id>/assign', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    approved_staff = User.query.filter_by(role='staff', approval_status='Approved', is_blacklisted=False).all()

    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        trek.assigned_staff_id = int(staff_id) if staff_id else None
        db.session.commit()
        flash('Staff assignment updated.', 'success')
        return redirect(url_for('admin.manage_treks'))

    return render_template('admin/assign_staff.html', trek=trek, staff_list=approved_staff)


@admin_bp.route('/staff')
@login_required
@role_required('admin')
def manage_staff():
    search_query = request.args.get('q', '').strip()

    staff_query = User.query.filter_by(role='staff')
    if search_query:
        if search_query.isdigit():
            staff_query = staff_query.filter(User.id == int(search_query))
        else:
            staff_query = staff_query.filter(User.name.ilike(f'%{search_query}%'))

    all_staff = staff_query.all()
    return render_template('admin/manage_staff.html', staff_list=all_staff, search_query=search_query)


@admin_bp.route('/staff/<int:user_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_staff(user_id):
    staff = User.query.get_or_404(user_id)
    staff.approval_status = 'Approved'
    db.session.commit()
    flash(f'{staff.name} has been approved.', 'success')
    return redirect(url_for('admin.manage_staff'))


@admin_bp.route('/users/<int:user_id>/blacklist', methods=['POST'])
@login_required
@role_required('admin')
def toggle_blacklist(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    status = 'blacklisted' if user.is_blacklisted else 'un-blacklisted'
    flash(f'{user.name} has been {status}.', 'info')

    if user.role == 'staff':
        return redirect(url_for('admin.manage_staff'))
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users')
@login_required
@role_required('admin')
def manage_users():
    search_query = request.args.get('q', '').strip()

    users_query = User.query.filter_by(role='trekker')
    if search_query:
        if search_query.isdigit():
            users_query = users_query.filter(User.id == int(search_query))
        else:
            users_query = users_query.filter(User.name.ilike(f'%{search_query}%'))

    all_users = users_query.all()
    return render_template('admin/manage_users.html', users=all_users, search_query=search_query)