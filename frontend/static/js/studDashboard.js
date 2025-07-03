import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import { getFirestore, collection, getDocs, doc, setDoc, addDoc, getDoc, deleteDoc, serverTimestamp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";
import { getStorage, ref, uploadBytesResumable, getDownloadURL } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-storage.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import { query, where } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyDWO1wHoJUv05yCZIrcK3CWpRcIpkVksvg",
  authDomain: "fyp-ai-3a972.firebaseapp.com",
  projectId: "fyp-ai-3a972",
  storageBucket: "fyp-ai-3a972.firebasestorage.app",
  messagingSenderId: "1095317736019",
  appId: "1:1095317736019:web:1fd2dafaea68314c9d54a6"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const storage = getStorage(app);
const auth = getAuth(app);

let currentAssignmentId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initializeDragAndDrop();
  loadStudentName();
});

function initializeDragAndDrop() {
  const dropArea = document.getElementById('drop-area');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');

  // Browse button click handler
  browseBtn.addEventListener('click', () => fileInput.click());

  // Prevent default drag behaviors
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // Highlight drop area when item is dragged over it
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });

  function highlight() {
    dropArea.classList.add('highlight');
  }

  function unhighlight() {
    dropArea.classList.remove('highlight');
  }

  // Handle dropped files
  dropArea.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    fileInput.files = files;
    handleFiles(files);
  }

  // Handle file selection via input
  fileInput.addEventListener('change', function() {
    handleFiles(this.files);
  });
}

function handleFiles(files) {
  if (files.length > 0) {
    const file = files[0];
    if (typeValidation(file.type)) {
      const fileList = document.getElementById('fileList');
      fileList.innerHTML = `
        <div>
          <span>${file.name}</span>
          <span>${(file.size / 1024).toFixed(2)} KB</span>
        </div>
      `;
      // Auto-upload after selection
      uploadSubmission(file);
    } else {
      alert('Only PDF and image files are allowed.');
    }
  }
}

function typeValidation(type) {
  const splitType = type.split('/')[0];
  return type === 'application/pdf' || splitType === 'image';
}

function openUploadModal(assignmentId) {
  currentAssignmentId = assignmentId;
  document.getElementById("uploadModal").classList.add('active');
}

function closeUploadModal() {
  document.getElementById("uploadModal").classList.remove('active');
  document.getElementById("fileInput").value = "";
  document.getElementById("fileList").innerHTML = "";
  document.getElementById('uploadProgress').style.width = '0%';
}

async function uploadSubmission(file) {
  if (!file) {
    file = document.getElementById('fileInput').files[0];
  }

  const studentSnap = await getDoc(doc(db, "students", auth.currentUser.uid));
if (!studentSnap.exists()) {
  alert("Student profile not found. Please contact support.");
  return;
}
const studentData = studentSnap.data();
const studentID = studentData.studentID;

  if (!file || !studentID || !currentAssignmentId) {
    alert("Please select a file and ensure you are logged in.");
    return;
  }

  try {
    const storagePath = `submissions/${auth.currentUser.uid}/${currentAssignmentId}/${file.name}`;
    const storageRef = ref(storage, storagePath);
    const uploadTask = uploadBytesResumable(storageRef, file);

    uploadTask.on('state_changed',
      (snapshot) => {
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        document.getElementById('uploadProgress').style.width = progress + '%';
      },
      (error) => {
        console.error("Upload failed:", error);
        alert("Upload failed: " + error.message);
      },
      async () => {
        const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
        await setDoc(doc(db, "submissions", `${studentID}_${currentAssignmentId}`), {
        studentID,
          assignmentID: currentAssignmentId,
          assignmentTitle: assignmentData.title, // Store title with submission
          fileURL: downloadURL,
          submittedAt: serverTimestamp(),
          status: "submitted",
          grade: "",
          classCode: assignmentData.classCode // Also store class code for filtering
        });
        alert("Submission uploaded successfully!");
        closeUploadModal();
        loadAssignments(); // Refresh assignments list
      }
    );
  } catch (error) {
    console.error("Error uploading:", error);
    alert("Error: " + error.message);
  }
}

// Auth state and student data handling
onAuthStateChanged(auth, async (user) => {
  if (user) {
    let docRef = doc(db, "students", user.uid);
    let docSnap = await getDoc(docRef);

    if (!docSnap.exists()) {
      const allStudents = await getDocs(collection(db, "students"));
      for (const oldDoc of allStudents.docs) {
        const data = oldDoc.data();
        if (data.email === user.email) {
          await setDoc(doc(db, "students", user.uid), data);
          await deleteDoc(doc(db, "students", oldDoc.id));
          console.log(`✅ Migrated ${user.email} to UID ${user.uid}`);
          docSnap = await getDoc(doc(db, "students", user.uid));
          break;
        }
      }
    }
    
    await loadAssignments();

    if (docSnap.exists()) {
      const data = docSnap.data();
      localStorage.setItem("studentID", data.studentID);
      localStorage.setItem("studentData", JSON.stringify(data));
      loadStudentName();
    } else {
      console.warn("⚠️ Student data still not found. May cause issues in submissions.");
    }
  }
});

function loadStudentName() {
  const studentData = JSON.parse(localStorage.getItem("studentData"));

  if (studentData && studentData.firstname) {
    document.getElementById("student-greeting").innerText = `Hello, ${studentData.firstname}`;
  } else {
    document.getElementById("student-greeting").innerText = "Hello, Student";
  }
}

async function loadAssignments() {
  const accordionDiv = document.getElementById("assignmentAccordion");
  const today = new Date();
  accordionDiv.innerHTML = '';

  const studentData = JSON.parse(localStorage.getItem("studentData"));
  const classCode = studentData?.joinedClass?.code;

  if (!classCode) {
    accordionDiv.innerHTML = "<p style='text-align: center; color: #666;'>No class assigned.</p>";
    return;
  }

  const q = query(collection(db, "assignments"), where("classCode", "==", classCode));
  const assignmentsSnapshot = await getDocs(q);

  let hasAssignments = false;
  const uid = auth.currentUser.uid;

  for (const assignmentDoc of assignmentsSnapshot.docs) {
    const data = assignmentDoc.data();
    const assignmentId = assignmentDoc.id;
    
    // SAFELY HANDLE DUE DATE
    let dueDate;
    try {
      // Check if dueDate exists and is a Firestore Timestamp
      if (data.dueDate && typeof data.dueDate.toDate === 'function') {
        dueDate = data.dueDate.toDate();
      } else if (data.dueDate?.seconds) {
        // Alternative format (if stored as {seconds, nanoseconds})
        dueDate = new Date(data.dueDate.seconds * 1000);
      } else if (data.dueDate) {
        // If it's already a Date object or string
        dueDate = new Date(data.dueDate);
      }
    } catch (e) {
      console.error("Error parsing due date:", e);
      continue; // Skip this assignment if date is invalid
    }

    if (!dueDate || isNaN(dueDate.getTime())) {
      console.warn(`Invalid due date for assignment ${assignmentId}`, data.dueDate);
      continue;
    }

    // Only show upcoming assignments
    if (dueDate >= today) {
      hasAssignments = true;
      const title = data.title || `Assignment #${assignmentId.slice(0,4)}`; 
      const description = data.description || "No description available.";
      const fileURL = data.assignmentFileURL || "#";
      const daysLeft = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
      const formattedDate = dueDate.toLocaleDateString("en-US", {
        year: "numeric", 
        month: "short", 
        day: "numeric"
      });

      // Rest of your code remains the same...
      const submissionId = `${uid}_${assignmentId}`;
      const submissionSnap = await getDoc(doc(db, "submissions", submissionId));

      let uploadButtonHTML = "";
      if (!submissionSnap.exists()) {
        uploadButtonHTML = `
          <button class="action-btn upload-btn" onclick="openUploadModal('${assignmentId}')">
            <i class="fas fa-upload"></i> Upload Submission
          </button>
        `;

      } else {
        const submission = submissionSnap.data();
        const rawStatus = submission?.status || "not submitted";
        const isReleased = submission?.released === true;
        const isGraded = rawStatus === "graded" && !!submission?.grade;

        if (isReleased && isGraded) {
          uploadButtonHTML = `
            <div class="graded-block">
              <span class="badge bg-success text-light">✅ Submitted</span>
              <div class="grading-info">
                <p><strong>Grade:</strong> ${submission.grade}</p>
                <p><strong>Feedback:</strong> ${submission.feedback}</p>
                ${submission.gradingFileURL ? `<a href="${submission.gradingFileURL}" target="_blank" class="view-assignment-btn">View Marked File</a>` : ''}
              </div>
            </div>
          `;
        } else {
          uploadButtonHTML = `
            <span class="badge bg-success text-light">✅ Submitted </span>
          `;
        }
      }

      // Create assignment HTML (make sure to add this part)
const assignmentHTML = `
  <div class="assignment-card shadow-sm">
    <div class="assignment-header">
      <h5 class="assignment-title">${title}</h5>
      <small class="assignment-due">📅 Due: ${formattedDate} <span class="due-label">(${daysLeft} days left)</span></small>
    </div>
    <p class="assignment-description">${description}</p>
    <div class="assignment-actions">
      ${fileURL ? `<a href="${fileURL}" target="_blank" class="btn-view">📄 View Assignment</a>` : ''}
      ${uploadButtonHTML}
    </div>
  </div>
`;

      accordionDiv.innerHTML += assignmentHTML;
    }
  }

  if (!hasAssignments) {
    accordionDiv.innerHTML = "<p style='text-align: center; color: #666;'>No upcoming assignments found.</p>";
  }
}

  // Accordion toggle functionality
  const items = document.querySelectorAll('.assignment-item');
  items.forEach(item => {
    const header = item.querySelector('.assignment-header');
    header.addEventListener('click', () => {
      items.forEach(other => {
        if (other !== item && other.classList.contains('active')) {
          other.classList.remove('active');
        }
      });
      item.classList.toggle('active');
    });
  });


async function markAsGraded(studentID, assignmentID, grade, feedback, gradingFileURL = "") {
  const submissionRef = doc(db, "submissions", `${studentID}_${assignmentID}`);
  await setDoc(submissionRef, {
    grade,
    feedback,
    released: true,
    status: "graded",
    gradingFileURL
  }, { merge: true });

  alert("✅ Grading saved for " + studentID);
}


// Expose functions to global scope
window.openUploadModal = openUploadModal;
window.closeUploadModal = closeUploadModal;
window.uploadSubmission = uploadSubmission;
window.markAsGraded = markAsGraded; 