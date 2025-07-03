// indexLecturer.js (non-module version for compatibility)
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";

import {getAuth,signOut, signInWithEmailAndPassword, updateProfile } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import { getFirestore, doc, setDoc, getDoc,serverTimestamp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-storage.js";
import { sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import {
  getDocs,
  collection,
  query,
  where,
  orderBy,   // ✅ Add this
  limit      // ✅ Add this
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";

// Firebase Config
const firebaseConfig = {
  apiKey: "AIzaSyDWO1wHoJUv05yCZIrcK3CWpRcIpkVksvg",
  authDomain: "fyp-ai-3a972.firebaseapp.com",
  projectId: "fyp-ai-3a972",
  storageBucket: "fyp-ai-3a972.firebasestorage.app",
  messagingSenderId: "1095317736019",
  appId: "1:1095317736019:web:1fd2dafaea68314c9d54a6",
  measurementId: "G-2Y9J22HNYN"
};


const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);


async function loadRecentSubmissions() {
  try {
    const container = document.getElementById('recent-submissions');
        console.log("🔁 Loading recent submissions...");

    if (!container) throw new Error('Container not found');
    
    // Show loading spinner
    container.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-warning"></div></div>';

    // Query submissions from Firebase
    const q = query(
      collection(db, 'submissions'),
      orderBy('submittedAt', 'desc'),
      limit(4) // Show 4 cards like in the image example
    );
        console.log("📡 Querying Firestore for recent submissions...");

    
    const snapshot = await getDocs(q);
    console.log("Documents found:", snapshot.docs.map(doc => doc.id));

    if (snapshot.empty) {
            console.warn("📭 No recent submissions found.");
      container.innerHTML = '<p class="text-muted">No recent submissions found.</p>';
      return;
    }

    container.innerHTML = '';
    
    snapshot.forEach(doc => {
      const data = doc.data();
      console.log("Document data:", data);
      
      // Date formatting (keep your existing date handling)
      let submittedDate;
      if (data.submittedAt?.toDate) {
        submittedDate = data.submittedAt.toDate();
      } else if (typeof data.submittedAt === 'string') {
        submittedDate = new Date(data.submittedAt);
      } else {
        submittedDate = new Date();
      }

      const formattedDate = submittedDate.toLocaleString('en-GB', {
        timeZone: 'Asia/Kuala_Lumpur',
        day: '2-digit', 
        month: 'short', 
        year: 'numeric'
      });

      // Extract day and month for the card layout
      const day = submittedDate.getDate();
      const month = submittedDate.toLocaleString('en-US', { month: 'short' }).toUpperCase();

      // Create card with layout similar to your image example
  const card = document.createElement('div');
  card.className = 'col-xl-3 col-lg-3 col-md-6 col-sm-6 mb-4'; // Adjusted for better horizontal layout

// In loadRecentSubmissions(), replace the status check with:
let statusBadgeHTML = "";
const status = data.status?.toLowerCase() || 'submitted';

if (status === "graded" || status === "released") {
  statusBadgeHTML = `<span class="badge rounded-pill" style="background-color:#28a745 !important; color:#fff !important; font-size:13px; font-weight:600;">Graded</span>`;
} else if (status === "submitted" || status === "pending") {
  statusBadgeHTML = `<span class="badge rounded-pill" style="background-color:#fde68a !important; color:#92400e !important; font-size:13px; font-weight:600;">Pending</span>`;
} else {
  statusBadgeHTML = `<span class="badge rounded-pill" style="background-color:#fca5a5 !important; color:#991b1b !important; font-size:13px; font-weight:600;">Not Submitted</span>`;
}

      
card.innerHTML = `
  <div class="card flex-fill shadow-sm h-100" style="border-radius: 16px; border: none;">
    <div class="card-body d-flex flex-column p-4" style="background-color: #fdfdfd; border-radius: 16px; border: 1px solid #e0e0e0;">
      
      <div class="text-end mb-2">
        <span class="badge rounded-pill" style="background-color: #a12c2f; color: white; font-size: 0.9rem;">
          ${data.grade ? `Grade: ${data.grade}` : 'Pending'}
        </span>
      </div>
      
      <div class="d-flex align-items-center mb-3">
        <div class="me-3 text-center" style="min-width: 60px;">
          <div style="background: linear-gradient(to bottom, #e0f2f1, #f8f9fa); padding: 8px; border-radius: 8px;">
            <div style="color: #165c56; font-size: 0.9rem;" class="fw-bold">${month}</div>
            <div class="fw-bold" style="font-size: 1.5rem;">${day}</div>
          </div>
        </div>
        <div>
          <h5 class="fw-bold mb-0" style="color: #165c56; font-size: 1.1rem; line-height: 1.3;">${data.assignmentTitle || 'Untitled Assignment'}</h5>
          <small class="text-muted">${data.studentName} (${data.studentID})</small>
        </div>
      </div>
      
      <p class="text-muted mb-3" style="font-size: 0.9rem; flex-grow: 1;">
        <strong>Status:</strong> ${data.status || 'Submitted'}
      </p>
      
      <div class="d-flex flex-column gap-2">
        <a href="${data.fileURL}" target="_blank" class="btn btn-sm w-100" 
           style="background-color: #165c56; color: white;"
           onmfouseover="this.style.backgroundColor='#0f3f3b'" 
           onmouseout="this.style.backgroundColor='#165c56'">
          📄 View Submission
        </a>
        ${data.gradingFileURL ? `
          <a href="${data.gradingFileURL}" target="_blank" class="btn btn-outline-secondary btn-sm w-100">
            📝 Grading
          </a>
        ` : ''}
      </div>
    </div>
  </div>
`;


      container.appendChild(card);
    });

  } catch (error) {
    console.error("Error:", error);
    const container = document.getElementById('recent-submissions');
    if (container) {
      container.innerHTML = `
        <div class="col-12 alert alert-danger">
          Failed to load submissions: ${error.message}
        </div>
      `;
    }
  }
}

/*Student submission*/
async function loadLecturerSubmissions() {
  console.log("🔁 Loading lecturer submissions...");

  const container = document.getElementById('lecturerSubmissionGrid');
  if (!container) return console.error("Container not found");

  container.innerHTML = `<div class="col-12 text-center"><div class="spinner-border text-primary"></div></div>`;

  try {
    const user = auth.currentUser;
    if (!user) {
      container.innerHTML = '<p class="text-muted">Not logged in.</p>';
      return;
    }

    const lecturerEmail = user.email;

        // Step 1: Query assignments by this lecturer
    const assignmentQuery = query(
      collection(db, 'assignments'),
      where('lecturer_email', '==', lecturerEmail)
    );
    const assignmentSnapshot = await getDocs(assignmentQuery);

    if (assignmentSnapshot.empty) {
      container.innerHTML = '<p class="text-muted">No assignments found for your account.</p>';
      return;
    }

        const assignmentIds = assignmentSnapshot.docs.map(doc => doc.id);

         let allSubmissionDocs = [];

    for (let i = 0; i < assignmentIds.length; i += 20) {
      const batchIds = assignmentIds.slice(i, i + 20);
      const submissionQuery = query(
        collection(db, 'submissions'),
        where('assignmentId', 'in', batchIds)
      );
      const submissionSnapshot = await getDocs(submissionQuery);
      allSubmissionDocs.push(...submissionSnapshot.docs);
    }

    if (allSubmissionDocs.length === 0) {
      container.innerHTML = '<p class="text-muted">No submissions found.</p>';
      return;
    }

    container.innerHTML = '';

      for (const docSnap of allSubmissionDocs) {
        const data = docSnap.data();
        const status = (data.status || 'submitted').toLowerCase();
        const isReleased = status === 'released';
          const isDisabled = status === 'released' ? 'disabled' : '';


        const badgeColor = {
          graded: 'bg-success',
          released: 'bg-secondary',
          pending: 'bg-warning',
          submitted: 'bg-info'
        }[status] || 'bg-light';


      const card = document.createElement('div');
      card.className = `col-md-6 col-lg-4 mb-4 mix ${status}`;

      card.innerHTML = `
        <div class="submission-card p-4 shadow-sm rounded-4">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <span class="badge ${badgeColor}">
              ${status.toUpperCase()}
            </span>

            <button class="btn btn-sm ${status === 'graded' ? 'btn-success' : 'btn-outline-secondary'}" 
                    onclick="loadSubmissionDetail('${docSnap.id}', '${status}')"
                    ${isDisabled}>
              ✏️ Edit
            </button>
          </div>
          <h6 class="assignment-title mb-2">${data.assignmentTitle || 'Untitled'}</h6>
          <p class="text-muted small m-0">
            ${data.studentName} (${data.studentID})<br>
            Class: ${data.classCode || 'N/A'}
          </p>
          <div class="mt-3 d-grid gap-2">
            <a href="${data.fileURL}" target="_blank" class="btn btn-sm btn-outline-primary">
              View Submission
            </a>
            ${data.gradingFileURL ? `
              <a href="${data.gradingFileURL}" target="_blank" class="btn btn-sm btn-outline-success">
                View Graded
              </a>
            ` : ''}
          </div>
        </div>
      `;

      container.appendChild(card);
    }

  } catch (err) {
    console.error("Error:", err);
    container.innerHTML = `
      <div class="alert alert-danger">
        Error loading submissions: ${err.message}
      </div>
    `;
  }
}


// Move this INSIDE the DOMContentLoaded event listener:
window.addEventListener('DOMContentLoaded', () => {
  console.log("✅ DOM fully loaded.");

  const recentContainer = document.getElementById('recent-submissions');
  const lecturerContainer = document.getElementById('lecturerSubmissionGrid');

  // Create detail container here
  const detailContainer = document.createElement('div');
  detailContainer.id = 'submission-detail';
  detailContainer.className = 'container my-5';
  document.querySelector('#lecturerSubmissions .container')?.appendChild(detailContainer);

  if (recentContainer) {
    console.log("📦 Found #recent-submissions container");
    loadRecentSubmissions();
  } else {
    console.warn("⚠️ #recent-submissions container not found.");
  }

  if (lecturerContainer) {
    console.log("📦 Found #lecturerSubmissionGrid container");
    onAuthStateChanged(auth, (user) => {
      if (user) {
        console.log("✅ User is logged in:", user.email);
        loadLecturerSubmissions();
      } else {
        lecturerContainer.innerHTML = '<p class="text-danger">Please login to view submissions.</p>';
      }
    });
  }
});



const detailContainer = document.createElement('div');
detailContainer.id = 'submission-detail';
detailContainer.className = 'container my-5';
document.querySelector('#lecturerSubmissions .container').appendChild(detailContainer);

// ✅ JavaScript (indexLecturer.js)
async function loadSubmissionDetail(docId, status) {
  const container = document.getElementById('submission-detail');
  container.innerHTML = '<div class="text-center"><div class="spinner-border text-info"></div></div>';

  try {
    const docSnap = await getDoc(doc(db, 'submissions', docId));
    if (!docSnap.exists()) {
      container.innerHTML = '<p class="text-danger">Submission not found.</p>';
      return;
    }

    const data = docSnap.data();
    const editable = (status.toLowerCase() !== 'released');


    container.innerHTML = `
      <div class="card shadow p-4 mt-4">
        <h4 class="mb-3 text-primary fw-bold">${data.assignmentTitle || 'Untitled Assignment'}</h4>
        <p><strong>Student:</strong> ${data.studentName} (${data.studentID})</p>
        <p><strong>Status:</strong> <span class="badge bg-${editable ? 'warning' : 'success'}">${data.status}</span></p>
        <p><strong>Grade:</strong></p>
        ${editable ? `<input type="text" id="edit-grade" class="form-control w-25 mb-3" value="${data.grade || ''}">` : `<p>${data.grade}</p>`}
        <p><strong>Feedback:</strong></p>
        ${editable ? `<textarea id="edit-feedback" class="form-control" rows="6">${data.feedback || ''}</textarea>` : `<pre class="bg-light p-3 border">${data.feedback || 'No feedback provided.'}</pre>`}
        <p class="mt-3"><strong>Submitted File:</strong> <a href="${data.fileURL}" target="_blank">📄 View File</a></p>
        ${data.gradingFileURL ? `<p><strong>Grading File:</strong> <a href="${data.gradingFileURL}" target="_blank">📝 View Grading</a></p>` : ''}
        ${editable ? `<button class="btn btn-success mt-4" onclick="saveFeedbackAndGrade('${docId}')">✅ Save & Mark Graded</button>` : ''}
        <button class="close-btn" onclick="document.getElementById('submission-detail').innerHTML = ''">✖</button>

      </div>
    `;

    // Auto scroll into view
    container.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    console.error(err);
    container.innerHTML = `<p class="text-danger">Failed to load submission detail.</p>`;
  }
}


async function saveFeedbackAndGrade(docId) {
  const gradeInput = document.getElementById('edit-grade');
  const feedbackInput = document.getElementById('edit-feedback');

  const grade = gradeInput.value.trim();
  const feedback = feedbackInput.value.trim();

  if (!grade) {
    alert("Please enter a grade");
    return;
  }

  // Single confirmation dialog
  const confirmRelease = confirm(`Release this grade to students?`);
  if (!confirmRelease) return;

  try {
    await setDoc(doc(db, 'submissions', docId), {
      grade,
      feedback,
      status: 'released', // Immediately set to released
      isReleased: true,   // Flag as released
      gradedAt: serverTimestamp(),
      releasedAt: serverTimestamp() // Same timestamp for immediate release
    }, { merge: true });

    alert("✅ Grades released to students!");
    loadLecturerSubmissions(); // Refresh the view
    document.getElementById('submission-detail').innerHTML = ''; // Close panel

  } catch (error) {
    console.error("Release failed:", error);
    alert("❌ Failed to release grades");
  }
}

async function releaseGradesToStudents(submissionId) {
  try {
    // First verify the submission exists and is graded
    const docRef = doc(db, 'submissions', submissionId);
    const docSnap = await getDoc(docRef);
    
    if (!docSnap.exists()) {
      throw new Error("Submission not found");
    }
    
    if (docSnap.data().status !== 'graded') {
      throw new Error("Submission must be graded before release");
    }

    // Confirmation with important info
    const confirmRelease = confirm(`Release this graded submission to student?\n\nGrade: ${docSnap.data().grade}\n\nThis action cannot be undone.`);
    if (!confirmRelease) return;

    // Perform release
    await setDoc(docRef, {
      status: 'released',
      isReleased: true,
      releasedAt: serverTimestamp()
    }, { merge: true });

    // UI Feedback
    alert("🎉 Grades successfully released to student!");
    loadLecturerSubmissions();

  } catch (error) {
    console.error("Release failed:", error);
    alert(`❌ Release failed: ${error.message}`);
  }
}

// Add to your lecturer UI (e.g., in a submission detail view):
function renderReleaseButton(submissionId, isReleased) {
  return `
    <button onclick="releaseGradesToStudents('${submissionId}')" 
            ${isReleased ? 'disabled' : ''}
            style="${isReleased ? 'opacity:0.5; cursor:not-allowed;' : ''}">
      ${isReleased ? '✓ Released' : 'Release to Student'}
    </button>
  `;
}



window.loadSubmissionDetail = loadSubmissionDetail;
window.saveFeedbackAndGrade = saveFeedbackAndGrade;


// ✅ Make logoutUser globally accessible
window.logoutUser = function () {
  signOut(auth)
    .then(() => {
      alert("✅ Logged out successfully!");
      window.location.href = "/signup";  // Use Flask route URL path
    })
    .catch((error) => {
      console.error("Logout error:", error);
      alert("❌ Logout failed.");
    });
};



//edit profile
// Initialize profile modal
document.addEventListener('DOMContentLoaded', function() {
  // Get the profile link and modal
  const profileLink = document.getElementById('profileLink');
  const profileModal = new bootstrap.Modal(document.getElementById('profileModal'));

  // Add click handler for profile link
  if (profileLink) {
    profileLink.addEventListener('click', function(e) {
      e.preventDefault();
      loadProfileData();
      profileModal.show();
    });
  }

  // Function to load profile data
  async function loadProfileData() {
    const user = auth.currentUser;
    if (!user) return;

    const nameElement = document.getElementById("lecturerName");
    const emailElement = document.getElementById("lecturerEmail");

    // Set email immediately
    if (emailElement) emailElement.textContent = user.email;

    try {
      const docRef = doc(db, "lecturers", user.uid);
      const docSnap = await getDoc(docRef);

      if (docSnap.exists()) {
        const name = docSnap.data().name || "No Name";
        if (nameElement) nameElement.textContent = name;
      } else {
        if (nameElement) nameElement.textContent = "Unknown Lecturer";
      }
    } catch (err) {
      console.error("Error loading profile:", err);
      if (nameElement) nameElement.textContent = "Error loading name";
    }
  }

});


