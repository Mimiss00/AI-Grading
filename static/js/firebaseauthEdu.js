

// Import Firebase SDKs
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import {
  getFirestore,
  doc,
  setDoc,
  getDoc
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-storage.js";

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyDWO1wHoJUv05yCZIrcK3CWpRcIpkVksvg",
  authDomain: "fyp-ai-3a972.firebaseapp.com",
  projectId: "fyp-ai-3a972",
  storageBucket: "fyp-ai-3a972.firebasestorage.app",
  messagingSenderId: "1095317736019",
  appId: "1:1095317736019:web:1fd2dafaea68314c9d54a6",
  measurementId: "G-2Y9J22HNYN"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// =========================
// Lecturer LOGIN HANDLER
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("lecturerLoginForm");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = loginForm.querySelector('input[name="email"]').value.trim();
      const password = loginForm.querySelector('input[name="password"]').value.trim();

      if (!email.endsWith("@lecturer.uitm.com")) {
        Swal.fire({
          icon: 'error',
          title: 'Invalid Email',
          text: 'Only @lecturer.uitm.com emails are allowed.'
        });
        return;
      }

      if (!email || !password) {
        Swal.fire({
          icon: 'warning',
          title: 'Missing Fields',
          text: 'Please enter both email and password.'
        });
        return;
      }

      try {
        const userCred = await signInWithEmailAndPassword(auth, email, password);
        const user = userCred.user;

        const docRef = doc(db, "lecturers", user.uid);
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
          await fetch('/save-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              role: 'lecturer',
              email: email
            })
          });

          Swal.fire({
            icon: 'success',
            title: 'Login Successful',
            text: 'Redirecting to your dashboard...',
            timer: 2000,
            showConfirmButton: false
          }).then(() => {
            window.location.href = "/lecturer/dashboard-edu";
          });

        } else {
          await signOut(auth);
          Swal.fire({
            icon: 'error',
            title: 'Profile Not Found',
            text: 'No lecturer profile found. Please register first.'
          });
        }

      } catch (error) {
        console.error(error);
        const code = error.code;
        let message = "Login failed. Please try again.";

        if (code === "auth/wrong-password") {
          message = "Wrong password. Please try again.";
        } else if (code === "auth/user-not-found") {
          message = "User not found. Please register.";
        } else if (code === "auth/too-many-requests") {
          message = "Too many failed attempts. Try again later.";
        } else if (code === "auth/invalid-email") {
          message = "Invalid email format.";
        } else if (code === "auth/invalid-credential") {
          message = "Invalid email or password.";
        }

        Swal.fire({
          icon: 'error',
          title: 'Login Failed',
          text: message
        });
      }
    });
  }

  // =========================
  // Lecturer REGISTER HANDLER
  // =========================
  const registerForm = document.getElementById("lecturerRegisterForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const name = document.getElementById("lecturerName").value.trim();
      const email = document.getElementById("lecturerEmail").value.trim();
      const password = document.getElementById("registerPassword").value.trim();

      if (!email.endsWith("@lecturer.uitm.com")) {
        Swal.fire({
          icon: 'error',
          title: 'Registration Failed',
          text: 'Only @lecturer.uitm.com emails are allowed.'
        });
        return;
      }

      if (!name || !email || !password) {
        Swal.fire({
          icon: 'warning',
          title: 'Missing Fields',
          text: 'Please fill in all fields.'
        });
        return;
      }

      try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        await setDoc(doc(db, "lecturers", user.uid), {
          name,
          email,
          createdAt: new Date().toISOString()
        });

        Swal.fire({
          icon: 'success',
          title: 'Registration Successful',
          text: 'Now you can log in.',
          timer: 2000,
          showConfirmButton: false
        }).then(() => {
          window.location.href = "/lecturer/login";
        });

      } catch (error) {
        console.error(error);
        Swal.fire({
          icon: 'error',
          title: 'Registration Failed',
          text: error.message
        });
      }
    });
  }
});
