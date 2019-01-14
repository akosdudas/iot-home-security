package pite.android.aut.bme.hu.raspberryapp

import android.content.Intent
import android.support.v7.app.AppCompatActivity
import android.os.Bundle
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.Switch
import kotlinx.android.synthetic.main.activity_main.*
import kotlinx.android.synthetic.main.activity_menu.*
import pite.android.aut.bme.hu.raspberryapp.network.RaspberryAPI

class ControlActivity : AppCompatActivity() {

    var linearLayout : LinearLayout? = null
    var switchesArray = arrayOf<Switch>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_menu)
        linearLayout = findViewById<LinearLayout>(R.id.switchContainer)
        val cookie = intent.getStringExtra("cookie")
        val _xsrf = intent.getStringExtra("xsrf")

        val raspberryAPI = RaspberryAPI.instance
        var zones = raspberryAPI.getZonesList()
        listSwitchesBasedOnZones(zones)
        btnStartPCA.setOnClickListener {

            async {

                raspberryAPI.startPCA(cookie,_xsrf,createHashMapofZones(zones))
            }
        }

        btnStopPCA.setOnClickListener {
            async {

                raspberryAPI.stopPCA(this)
            }
        }
    }

    /* Display zone switches on linear layout based on getzoneslist */
    private fun listSwitchesBasedOnZones(zones: MutableSet<String>) {
        for(zone in zones) {
            val switch = Switch(this)
            switch.setText(zone)
            switch.layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            switchesArray += switch
            linearLayout?.addView(switch)

        }

    }

    /* create a map of zones, with zone names and activites*/
    private fun createHashMapofZones(zones: MutableSet<String>) : HashMap<String,Boolean>{
        var zoneMap: HashMap<String, Boolean> = hashMapOf()
        var i = 0
        for(zone in zones) {
            switchesArray.elementAt(i).text.toString()
            println(switchesArray.elementAt(i).text.toString())
            zoneMap.put(switchesArray.elementAt(i).text.toString(),switchesArray.elementAt(i).isChecked())
            i++
            i++
        }
        return zoneMap
    }

    /* fucntion for async calls */
    private fun async(call: () -> String) {
        Thread {
            val response = call()
            runOnUiThread { showResponse(response) }
        }.start()
    }

    private fun showResponse(response: String) {
        tvResponse2.text = response
    }
}
