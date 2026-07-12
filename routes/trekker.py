from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Trek, Booking
from routes.decorators import role_required

trekker_bp = Blueprint('trekker', __name__, url_prefix='/trekker')


@trekker_bp.route('/dashboard')
@login_required
@role_required('trekker')
def dashboard():
    my_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('trekker/dashboard.html', bookings=my_bookings)


@trekker_bp.route('/treks')
@login_required
@role_required('trekker')
def browse_treks():
    query = Trek.query.filter_by(status='Open')

    location = request.args.get('location')
    difficulty = request.args.get('difficulty')

    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    treks = query.all()

    return render_template(
        'trekker/browse_treks.html',
        treks=treks,
        location=location or '',
        difficulty=difficulty or '',
    )


@trekker_bp.route('/treks/<int:trek_id>/book', methods=['POST'])
@login_required
@role_required('trekker')
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('trekker.browse_treks'))

    if trek.available_slots <= 0:
        flash('Sorry, this trek is fully booked.', 'danger')
        return redirect(url_for('trekker.browse_treks'))

    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status='Booked').first()
    if existing:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('trekker.browse_treks'))

    new_booking = Booking(user_id=current_user.id, trek_id=trek.id, status='Booked')
    trek.available_slots -= 1

    db.session.add(new_booking)
    db.session.commit()

    flash('Trek booked successfully!', 'success')
    return redirect(url_for('trekker.dashboard'))


@trekker_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required('trekker')
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        abort(403)

    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        booking.trek.available_slots += 1
        db.session.commit()
        flash('Booking cancelled.', 'info')

    return redirect(url_for('trekker.dashboard'))


@trekker_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('trekker')
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.contact_details = request.form.get('contact_details')
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('trekker.edit_profile'))

    return render_template('trekker/edit_profile.html')