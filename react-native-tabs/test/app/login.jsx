import { Text, View, TextInput, ActivityIndicator, KeyboardAvoidingView, TouchableOpacity } from 'react-native';
import React, {  useState} from "react"
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth"
import {db} from "../firebase"
import { router, useLocalSearchParams } from "expo-router"
import{FIREBASE_AUTH} from "../firebase"
import GoogleSignIn from "../components/GoogleSignIn"

const SignUp = () => {
    const {type} = useLocalSearchParams()
    const [email, setEmail] = useState("")
    
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const auth = FIREBASE_AUTH
    
    const signin = async() => {
        setLoading(true)
        try {
            const user = await signInWithEmailAndPassword(auth, email, password)
            if (user) router.replace('/(tabs)')
         }
        catch (error) { 
            console.log(error)
            alert("Sign in failed:"+ error.message)
        } finally { setLoading(false)
            
        }
    }

    const signup = async() => {
        setLoading(true)
        try {
            const user = await createUserWithEmailAndPassword(auth, email, password)
            if (user) router.replace('/(tabs)')
         }
        catch (error) { 
            console.log(error)
            alert("Sign in failed:"+ error.message)
        } finally { setLoading(false)
            
        }
    }
    

    return (
        <KeyboardAvoidingView>
            {loading ? <View>
  <ActivityIndicator size="large" color="#fff"/>
            </View>:""
            
        }
  

            <Text style={{color:"#fff"}}>  
                {type === "login" ? "Welcome Back": "Create Your Account"}
            </Text>
            <View>

                <TextInput
                autoCapitalize="none"
                    placeholder="Email"
                    value={email}
                    onChangeText={setEmail}

                />
                 <TextInput
                autoCapitalize="none"
                    placeholder="Password"
                value={password}
                onChangeText={setPassword}
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
            <GoogleSignIn/>
   
   </KeyboardAvoidingView> 
)
}
export default SignUp;