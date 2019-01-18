package pite.android.aut.bme.hu.raspberryapp

import android.content.Intent
import android.support.v7.app.AppCompatActivity
import android.os.Bundle
import android.view.View
import android.widget.EditText
import kotlinx.android.synthetic.main.activity_main.*
import pite.android.aut.bme.hu.raspberryapp.network.RaspberryAPI
import java.util.*

class MainActivity : AppCompatActivity() {

    var raspberryAPI = RaspberryAPI.instance
    var counter = 0;

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        btnLogin.setOnClickListener {
            raspberryAPI.setURL(etIPAddress.text.toString())
                async {
                    raspberryAPI.getMainPage(etIPAddress.text.toString()) // get main page
                    raspberryAPI.postPass(etPassword.text.toString()) // login
                    raspberryAPI.getZones()
                    val intent = Intent(this,ControlActivity::class.java)
                    intent.putExtra("cookie",raspberryAPI.csrf_token)
                    intent.putExtra("xsrf", raspberryAPI._xsrf)
                    startActivity(intent)
                }
        }
    }

    fun getCookie() :String {
        return raspberryAPI.csrf_token
    }

    private fun showResponse(response: String) {
       // tvResponse.text = response
        //mywebview!!.loadUrl(response)
    }

    private fun async(call: () -> Unit) {
        Thread {
            val response = call()
            runOnUiThread { counter++ }
        }.start()
    }
}
