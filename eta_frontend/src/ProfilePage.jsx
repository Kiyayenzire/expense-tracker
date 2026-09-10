import { useEffect, useMemo, useState } from 'react';

const initialProfile = {
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  phone_number: '',
  monthly_income: '0.00',
  profile_picture_url: '',
};

export default function ProfilePage({ token, onLogout, theme, setTheme, onNavigate, username, profilePicture, setProfilePicture, setUsername }) {
  const [profile, setProfile] = useState(initialProfile);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');

  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api', []);

  useEffect(() => {
    async function fetchProfile() {
      setLoading(true);
      try {
        const response = await fetch(`${apiBase}/auth/profile/`, {
          headers: {
            Authorization: `Token ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Unable to load profile.');
        }

        const data = await response.json();
        setProfile({
          username: data.username || '',
          email: data.email || '',
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          phone_number: data.phone_number || '',
          monthly_income: data.monthly_income || '0.00',
          profile_picture_url: data.profile_picture_url || '',
        });
        if (data.profile_picture_url) {
          localStorage.setItem('expense-tracker-profile-picture', data.profile_picture_url);
          setPreviewUrl(data.profile_picture_url);
          setProfilePicture(data.profile_picture_url);
        } else {
          localStorage.removeItem('expense-tracker-profile-picture');
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load profile information.');
      } finally {
        setLoading(false);
      }
    }

    if (token) fetchProfile();
  }, [apiBase, token, setProfilePicture]);

  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleImageChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }

    const objectUrl = URL.createObjectURL(file);
    setSelectedImage(file);
    setPreviewUrl(objectUrl);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      formData.append('first_name', profile.first_name || '');
      formData.append('last_name', profile.last_name || '');
      formData.append('phone_number', profile.phone_number || '');
      formData.append('monthly_income', profile.monthly_income || '0.00');
      if (selectedImage) {
        formData.append('profile_picture', selectedImage);
      }

      const response = await fetch(`${apiBase}/auth/profile/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Token ${token}`,
        },
        body: formData,
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = data.detail || data.non_field_errors?.[0] || 'Unable to save profile changes.';
        throw new Error(message);
      }

      const nextPicture = data.profile_picture_url || data.profile_picture || profilePicture || '';
      const nextUsername = data.username || username || 'User';
      if (nextPicture) {
        localStorage.setItem('expense-tracker-profile-picture', nextPicture);
      } else {
        localStorage.removeItem('expense-tracker-profile-picture');
      }
      localStorage.setItem('expense-tracker-username', nextUsername);
      setProfilePicture(nextPicture);
      setUsername(nextUsername);
      setProfile((current) => ({
        ...current,
        username: data.username || current.username,
        email: data.email || current.email,
        profile_picture_url: nextPicture,
      }));
      setPreviewUrl(nextPicture);
      setSelectedImage(null);
      setSuccess('Profile updated successfully.');
    } catch (submitError) {
      setError(submitError.message || 'Unable to save profile changes.');
    } finally {
      setSaving(false);
    }
  };

  const profileImage = previewUrl || profile.profile_picture_url || profilePicture || '';

  return (
    <div className="container">
      <main className="page-content">
        <section className="card profile-page-card">
          <div className="page-heading">
            <h2>My Profile</h2>
            <p className="small-text">Update your account details and profile photo.</p>
          </div>

          {error && <div className="alert alert-danger">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {loading ? (
            <p className="small-text">Loading profile…</p>
          ) : (
            <form onSubmit={handleSubmit} className="profile-form">
              <div className="profile-editor-header">
                <div className="profile-page-picture" style={{ width: '3rem', height: '3rem', flex: '0 0 3rem', overflow: 'hidden', borderRadius: '50%' }}>
                  {profileImage ? (
                    <img src={profileImage} alt="Profile" style={{ display: 'block', width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <div className="profile-avatar large-avatar">{(username || profile.username || 'User').slice(0, 2).toUpperCase()}</div>
                  )}
                </div>

                <div className="profile-upload-block">
                  <label className="form-label" htmlFor="profile-image-upload">Profile photo</label>
                  <input id="profile-image-upload" className="form-control" type="file" accept="image/*" onChange={handleImageChange} />
                  <small className="text-muted">Optional. JPG, PNG, or GIF under a standard image size.</small>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="profile-username">Username</label>
                  <input id="profile-username" className="form-control" type="text" value={profile.username} disabled />
                </div>
                <div className="form-group">
                  <label htmlFor="profile-email">Email</label>
                  <input id="profile-email" className="form-control" type="email" value={profile.email} disabled />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="profile-first-name">First name</label>
                  <input id="profile-first-name" className="form-control" type="text" value={profile.first_name} onChange={(event) => setProfile((current) => ({ ...current, first_name: event.target.value }))} />
                </div>
                <div className="form-group">
                  <label htmlFor="profile-last-name">Last name</label>
                  <input id="profile-last-name" className="form-control" type="text" value={profile.last_name} onChange={(event) => setProfile((current) => ({ ...current, last_name: event.target.value }))} />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="profile-phone">Phone number</label>
                <input id="profile-phone" className="form-control" type="tel" value={profile.phone_number} onChange={(event) => setProfile((current) => ({ ...current, phone_number: event.target.value }))} />
              </div>

              <div className="form-group">
                <label htmlFor="profile-monthly-income">Monthly income</label>
                <input id="profile-monthly-income" className="form-control" type="number" min="0" step="0.01" value={profile.monthly_income} onChange={(event) => setProfile((current) => ({ ...current, monthly_income: event.target.value }))} />
                <small className="text-muted">Used for budget recommendations.</small>
              </div>

              <div className="profile-actions">
                <button type="button" className="secondary-action-button" onClick={() => onNavigate('dashboard')}>Back to dashboard</button>
                <button type="submit" className="primary-action-button" disabled={saving}>{saving ? 'Saving…' : 'Save profile'}</button>
              </div>
            </form>
          )}
        </section>
      </main>
    </div>
  );
}
