﻿using UnityEngine;
using UnityEngine.InputSystem;

public class GravityGun : EnvironmentComponent
{

    [Header("Inputs")]
    bool getLeftMouseButton;
    bool getRightMouseButton;
    Vector3 mousePosition;

    [Header("Misc")]
    public float holdDistance = 2.0f;   // Distance from player's camera
    public float pullingSpeed = 2.0f;  // Speed to pull object
    public float throwingImpulse = 10.0f;  // Impulse to throw object away
    public float holdRange = 0.5f;
    public float snapDistance = 0.1f;
    public LayerMask objectLayerMask;  // Only consider objects on this layer
    public Color debugLineColor = Color.cyan;  // Color of the debug line

    private Rigidbody heldObject;
    private Vector3 targetPosition;
    private Camera playerCamera;

    bool mHadLeftClick = false;
    bool mHadRightClick = false;

    protected override void Start()
    {
        base.Start();
        playerCamera = Camera.main;
    }

    public override void StoreUserInputs()
    {
        getLeftMouseButton = GetInputPressedThisUpdate("Grab");
        getRightMouseButton = GetInputPressedThisUpdate("Drop");
        // TODO: just set to zero?
        // mousePosition is middle of screen
        mousePosition = new Vector2(Screen.width / 2, Screen.height / 2);
    }

    public override void OnFixedUpdate(float fixedDeltaTime)
    {
        if (getLeftMouseButton)
        {
            mHadLeftClick = true;
            mHadRightClick = false;
        }
        if (getRightMouseButton)
        {
            mHadRightClick = true;
            mHadLeftClick = false;
        }

        if (mHadRightClick)
        {
            if (heldObject != null)
            {
                // Drop the held object away
                heldObject.useGravity = true;  // Enable gravity
                heldObject = null;
            }
        }
        if (mHadLeftClick)
        {
            if (heldObject == null)
            {
                // Find the closest object with a rigidbody using a mouse raycast
                Ray mouseRay = playerCamera.ScreenPointToRay(mousePosition);
                RaycastHit hitInfo;
                float closestDistance = Mathf.Infinity;
                Rigidbody closestObject = null;
                if (Physics.Raycast(mouseRay, out hitInfo, Mathf.Infinity, objectLayerMask))
                {
                    Collider[] hitColliders = Physics.OverlapSphere(hitInfo.point, 0.1f, objectLayerMask);
                    foreach (Collider hitCollider in hitColliders)
                    {
                        Rigidbody hitRigidbody = hitCollider.GetComponent<Rigidbody>();
                        if (hitRigidbody != null)
                        {
                            float distance = Vector3.Distance(transform.position, hitCollider.transform.position);
                            if (distance < closestDistance)
                            {
                                closestDistance = distance;
                                closestObject = hitRigidbody;
                            }
                        }
                    }
                }

                if (closestObject != null)
                {
                    heldObject = closestObject;
                    heldObject.useGravity = false; // Disable gravity

                }
            }
            else
            {
                // Throw the held object away
                heldObject.useGravity = true;  // Enable gravity
                heldObject.AddForce(playerCamera.transform.forward * throwingImpulse, ForceMode.Impulse);
                heldObject = null;
            }
        }

        if (heldObject != null)
        {
            targetPosition = playerCamera.transform.position + playerCamera.transform.forward * holdDistance;

            // Move the held object towards the hold position
            Vector3 forceDirection = targetPosition - heldObject.transform.position;
            float forceMagnitude = pullingSpeed;
            if (forceDirection.magnitude < holdRange)
            {
                if (forceDirection.magnitude < snapDistance)
                {
                    heldObject.AddForce(-heldObject.velocity, ForceMode.VelocityChange);
                }
                else
                {
                    //forceMagnitude = Mathf.Pow(forceDirection.magnitude / holdRange, 0.5f) * pullingSpeed;

                    heldObject.velocity = heldObject.velocity.normalized * Mathf.Min(forceDirection.magnitude * pullingSpeed, heldObject.velocity.magnitude);

                    heldObject.AddForce(-heldObject.velocity * 0.2f, ForceMode.VelocityChange);

                    heldObject.AddForce(forceDirection.normalized * forceMagnitude, ForceMode.Force);
                }
            }
            else
            {
                heldObject.AddForce(-heldObject.velocity * 0.05f, ForceMode.VelocityChange);

                heldObject.AddForce(forceDirection.normalized * forceMagnitude, ForceMode.Force);
            }

            heldObject.angularVelocity *= 0.99f;
        }

        // Draw the mouse ray on the screen using a debug line
        Ray debugRay = playerCamera.ScreenPointToRay(mousePosition);
        Debug.DrawRay(debugRay.origin, debugRay.direction * 100.0f, debugLineColor);

        mHadLeftClick = false;
        mHadRightClick = false;
    }
}