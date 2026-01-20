import { Text, View, TextInput, ActivityIndicator, KeyboardAvoidingView, TouchableOpacity } from 'react-native';
import React, {  } from "react"
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth"
import {db} from "../firebase"
import {router } from "expo-router"


const SignUp = () => {
    const [email, setEmail] = useState("")
    
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const auth = db
    
    const signin = async() => {
        setLoading(true)
        try {
            const user = await signInWithEmailAndPassword(auth, email, password)
            if (user) router.replace('/(tabs)')
         }
        catch (error) { 
            console.log(error)
            alert("Sign in failed:"+ error.message)
        }
    }

    const singup = async() => {
        setLoading(true)
        try {
            const user = await createUserWithEmailAndPassword(auth, email, password)
            if (user) router.replace('/(tabs)')
         }
        catch (error) { 
            console.log(error)
            alert("Sign in failed:"+ error.message)
        }
    }
    

    return (
        <KeyboardAvoidingView>
            {loading ? <View>
  <ActivityIndicator size="large" color="#fff"/>
            </View>:""
            
        }
  

            <Text>
                {type === "login" ? "Welcome Back": "Create Your Account"}
            </Text>
            <View>

                <TextInput
                autoCapitalize="none"
                    placeholder="Email"
                    value={email}
                    onChange={setEmail}

                />
                 <TextInput
                autoCapitalize="none"
                    placeholder="Password"
                value={setPassword}

                />
            </View>

            {type === "login" ?
                <TouchableOpacity onPress={signin}>
                    <Text>Login</Text>
                </TouchableOpacity> :
                <TouchableOpacity onPress={signup}>
                    <Text>Create Account</Text>
            </TouchableOpacity>
        }
   
   </KeyboardAvoidingView> 
)
}
export default SignUp;