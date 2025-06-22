
// Import Firebase SDKs
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import {getAuth,createUserWithEmailAndPassword, 
        signInWithEmailAndPassword, updateProfile } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import { getFirestore, doc, setDoc, getDoc } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-storage.js";
import { sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";
import {
  getDocs,
  collection,
  query,  // ✅ This must be here!
  where
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";


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

document.addEventListener("DOMContentLoaded", () => {

  // =========================
  // Student LOGIN HANDLER
  // =========================

const loginForm = document.getElementById("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = loginForm.querySelector('input[name="email"]').value.trim();
    const password = loginForm.querySelector('input[name="password"]').value.trim();

    if (!email.endsWith("@student.uitm.edu.my")) {
      Swal.fire({
        icon: 'error',
        title: 'Login Failed',
        text: 'Only @student.uitm.edu.my emails are allowed for login.'
      });
      return;
    }

    Swal.fire({
      title: 'Logging in...',
      allowOutsideClick: false,
      didOpen: () => Swal.showLoading()
    });

    try {
      const userCred = await signInWithEmailAndPassword(auth, email, password);
      const user = userCred.user;

        const docRef = doc(db, "students", user.uid);
      const docSnap = await getDoc(docRef);

      // 🔄 If not found, try to find by email
   

      if (docSnap.exists()) {
        const studentData = docSnap.data();

       localStorage.setItem("studentData", JSON.stringify({
        firstname: studentData.firstname,
        studentID: studentData.studentID,
        uid: user.uid,                // ✅ optional, for profile updates
        email: user.email             // ✅ optional, for convenience
      }));

        await fetch('/save-session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            role: 'student',
            email: email
          })
        });

        Swal.fire({
          icon: 'success',
          title: 'Login Successful!',
          text: 'Welcome back!',
          timer: 1500,
          showConfirmButton: false
        }).then(() => {
          window.location.href = "/student/dashboard";
        });

      } else {
        await auth.signOut();
        Swal.fire({
          icon: 'error',
          title: 'Login Failed',
          text: 'Student profile not found. Please register properly.'
        });
      }

    } catch (error) {
      console.error(error);
      Swal.fire({
        icon: 'error',
        title: 'Login Failed',
        text: error.message
      });
    }
  }); // ✅ this closes loginForm.addEventListener
} // ✅ this closes if (loginForm)


  // =========================
  // Student REGISTER HANDLER
  // =========================
  const registerForm = document.getElementById("registerForm");

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const fullName = document.getElementById("fName").value.trim();
      const studentID = document.getElementById("studID").value.trim();
      const email = document.getElementById("sEmail").value.trim();
      const password = document.getElementById("registerPassword").value.trim();

      if (!email.endsWith("@student.uitm.edu.my")) {
        Swal.fire({
          icon: 'error',
          title: 'Registration Failed',
          text: 'Only @student.uitm.edu.my emails are allowed for registration.'
        });
        return;
      }

      Swal.fire({
        title: 'Registering...',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
      });

      try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        await updateProfile(user, {
          displayName: fullName
        });

        await setDoc(doc(db, "students", user.uid), {
          firstname: fullName,
          studentID: studentID,
          email: email
        });

        Swal.fire({
          icon: 'success',
          title: 'Registration Successful!',
          text: 'Now you can login!'
        }).then(() => {
          window.location.href = "/student/login";
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

    // =========================
  // FORGOT PASSWORD HANDLER
  // =========================
  const forgotPasswordLink = document.getElementById("forgotPasswordLink");

if (forgotPasswordLink) {
  forgotPasswordLink.addEventListener("click", async (e) => {
    e.preventDefault();

    const { value: email } = await Swal.fire({
      title: 'Reset Password',
      input: 'email',
      inputLabel: 'Enter your registered student email',
      inputPlaceholder: 'example@student.uitm.edu.my',
      inputAttributes: {
        autocapitalize: 'off',
        autocorrect: 'off'
      },
      showCancelButton: true,
      confirmButtonText: 'Send Reset Email',
      showLoaderOnConfirm: true,
      preConfirm: async (email) => {
        if (!email.endsWith("@student.uitm.edu.my")) {
          Swal.showValidationMessage("Only @student.uitm.edu.my emails are allowed.");
          return;
        }

        try {
          // 🔍 Check if email exists in Firestore
          const q = query(collection(db, "students"), where("email", "==", email));
          const querySnapshot = await getDocs(q);

          if (querySnapshot.empty) {
            Swal.showValidationMessage("No account found with that email.");
            return;
          }

          // ✅ Send reset email
          await sendPasswordResetEmail(auth, email);
        } catch (error) {
          console.error(error);
          Swal.showValidationMessage(error.message);
        }
      },
      allowOutsideClick: () => !Swal.isLoading()
    });

    if (email) {
      Swal.fire(
        'Success!',
        'A password reset email has been sent.',
        'success'
      );
    }
  });
}

});
