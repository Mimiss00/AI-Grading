import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import { getFirestore, collection, getDocs, doc, setDoc, addDoc, getDoc, serverTimestamp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";
import { getStorage, ref, uploadBytesResumable, getDownloadURL } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-storage.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js"; // ✅ Add this line
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";


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

onAuthStateChanged(auth, async (user) => {
  if (user) {
    let docRef = doc(db, "students", user.uid);
    let docSnap = await getDoc(docRef);

    // 🔄 Try fallback if doc not found by UID
    if (!docSnap.exists()) {
      const allStudents = await getDocs(collection(db, "students"));
      for (const oldDoc of allStudents.docs) {
        const data = oldDoc.data();
        if (data.email === user.email) {
          await setDoc(doc(db, "students", user.uid), data);  // copy
          await deleteDoc(doc(db, "students", oldDoc.id));     // delete old
          console.log(`✅ Migrated ${user.email} to UID ${user.uid}`);
          docSnap = await getDoc(doc(db, "students", user.uid));
          break;
        }
      }
    }

    if (docSnap.exists()) {
      const data = docSnap.data();
      localStorage.setItem("studentID", data.studentID);
      localStorage.setItem("studentData", JSON.stringify(data));
    } else {
      console.warn("⚠️ Student data still not found. May cause issues in submissions.");
    }
  }
});


let currentAssignmentId = null;

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
}

// 👇 expose globally
window.openUploadModal = openUploadModal;
window.closeUploadModal = closeUploadModal;


function loadStudentName() {
  const studentData = JSON.parse(localStorage.getItem("studentData"));

  if (studentData && studentData.firstname) {
    document.getElementById("student-greeting").innerText = `Hello, ${studentData.firstname}`;
  } else {
    console.warn("Student data not found in localStorage.");
    document.getElementById("student-greeting").innerText = "Hello, Student";
  }
}


async function uploadSubmission() {
  const file = document.getElementById('fileInput').files[0];
  const studentID = localStorage.getItem("studentID");

  if (!file || !studentID || !currentAssignmentId) {
    alert("Please select a file and ensure you are logged in.");
    return;
  }

  const confirmBtn = document.getElementById('confirmUpload');
  confirmBtn.disabled = true;

  try {
    const storagePath = `submissions/${studentID}/${currentAssignmentId}/${file.name}`;
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
        confirmBtn.disabled = false;
      },
      async () => {
        const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
      await setDoc(doc(db, "submissions", `${studentID}_${currentAssignmentId}`), {
          studentID,
          assignmentID: currentAssignmentId,
          fileURL: downloadURL,
          submittedAt: new Date().toISOString(),
          status: "submitted",
          grade: ""
        });

        alert("Submission uploaded successfully!");
        closeUploadModal();
        updateStats();
      }
    );
  } catch (error) {
    console.error("Error uploading:", error);
    alert("Error: " + error.message);
    confirmBtn.disabled = false;
  }
}

async function loadAssignments() {
  const accordionDiv = document.getElementById("assignmentAccordion");
  const today = new Date();
  const assignmentsSnapshot = await getDocs(collection(db, "assignments"));
  let hasAssignments = false;

  accordionDiv.innerHTML = '';

  assignmentsSnapshot.forEach((doc) => {
    const data = doc.data();
    const dueDate = new Date(data.dueDate);

    if (dueDate >= today) {
      hasAssignments = true;
      const title = data.title || "Untitled";
      const description = data.description || "No description available.";
      const fileURL = data.assignmentFileURL || "#";
      const daysLeft = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
      const formattedDate = dueDate.toLocaleDateString("en-US", {
        year: "numeric", month: "short", day: "numeric"
      });

      const assignmentItem = document.createElement('div');
      assignmentItem.classList.add('assignment-item');

   assignmentItem.innerHTML = `
        <div class="assignment-header">
          <div class="assignment-info">
            <h4>${title}</h4>
            <div class="due-date">
              <span>Due: ${formattedDate}</span>
              <span class="days-left">${daysLeft} ${daysLeft === 1 ? 'day' : 'days'} left</span>
            </div>
          </div>
          <button class="toggle-btn"><i class="fas fa-chevron-down"></i></button>
        </div>
        <div class="assignment-details">
          <p>Desc: ${description}</p>
          <a href="${fileURL}" target="_blank" class="view-assignment-btn">View Assignment</a>
          <button class="action-btn upload-btn" onclick="openUploadModal('${doc.id}')">
            <i class="fas fa-upload"></i> Upload Submission
          </button>
        </div>
      `;

      accordionDiv.appendChild(assignmentItem);
    }
  });

  if (!hasAssignments) {
    accordionDiv.innerHTML = "<p style='text-align: center; color: #666;'>No upcoming assignments found.</p>";
  }

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
}

async function updateStats() {
  const studentID = localStorage.getItem("studentID");
  if (!studentID) return;

  const assignmentsSnapshot = await getDocs(collection(db, "assignments"));
  const submissionsSnapshot = await getDocs(collection(db, "submissions"));

  console.log("✅ Student ID from localStorage:", studentID);
  console.log("📘 Assignments count:", assignmentsSnapshot.size);
  console.log("📗 Submissions count:", submissionsSnapshot.size);

  let totalCount = 0;
  let submittedCount = 0;
  let notSubmittedCount = 0;
  let gradeTotal = 0;
  let gradeCount = 0;
  const submissionsMap = {};

  submissionsSnapshot.forEach((doc) => {
    const data = doc.data();
    if (data.studentID === studentID) {
      submissionsMap[data.assignmentID] = data;
    }
  });

  assignmentsSnapshot.forEach((doc) => {
    const assignmentID = doc.id;
    totalCount++;
    const submission = submissionsMap[assignmentID];

    if (submission && submission.status === "submitted") {
      submittedCount++;
      const grade = submission.grade || "";
      if (grade.includes("/")) {
        const [scored, max] = grade.split("/").map(Number);
        if (!isNaN(scored) && !isNaN(max) && max > 0) {
          gradeTotal += (scored / max) * 100;
          gradeCount++;
        }
      }
    } else {
      notSubmittedCount++;
    }
  });

  const average = gradeCount > 0 ? (gradeTotal / gradeCount).toFixed(2) : "--";

  document.getElementById("totalCount").innerText = totalCount;
  document.getElementById("submittedCount").innerText = submittedCount;
  document.getElementById("notSubmittedCount").innerText = notSubmittedCount;
  document.getElementById("averageGrade").innerText = average + "%";
}


window.addEventListener('DOMContentLoaded', async () => {
  await loadStudentName();   // <--- Missing
  await loadAssignments();   // <--- Missing
  await updateStats();       // <--- Optional, but recommended
});